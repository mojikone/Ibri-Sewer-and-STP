# Adversarial review of `_BRAIN/08_DESIGN_PHILOSOPHY.md`

**Reviewed 2026-09-02 against the guideline PDFs read at source, `02_DESIGN_CRITERIA.md`,
`07_PROJECT_STATE.md`, `TUTORIALS/T02` and the nine research documents in this folder.**

The question asked was narrow: is this document fit to be a **binding project source** that
the next engineer designs 1,883 km of sewer from. It is reviewed as a specification, not as
an essay.

**Answer: NO — not yet.** The judgement in it is good and most of it should survive. But it
carries a hard constraint whose number contradicts the guideline it cites, it omits a
mandatory velocity requirement entirely, it states its central rule in a unit different from
the one its own evidence was measured in, about a dozen of its measured claims cannot be
traced to anything in the repository, and the whole of §9 rests on knowledge-base articles and
named-staff quotations that appear nowhere in the two research files it names as its sources.
Its audit registry does not test four of the twelve constraints it calls non-negotiable, and
would have passed W10 on the very defect it holds up as W10's worst.

Method: every PAM-GUD-203 number quoted below was re-extracted from
`Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf` with PyMuPDF during this review,
not taken from `02` or from a research file. Traceability searches covered every `.md`, `.py`,
`.csv` and `.txt` under `W10/` and `_BRAIN/`.

The shortest list of changes that would make it fit is at the end: **eight items, six of them
edits.**

---

## CRITICAL

Findings C4, C5 and C8 are one family — **evidence that cannot be checked** — and together
they are the reason the verdict is "no" rather than "yes with corrections".

### C1 — §6a H10 doubles a mandatory construction tolerance

**What is wrong.** H10 reads *"No reverse gradient; **40 mm** construction tolerance absorbed
| G203-p29 4.3.1"*. The source says 20 mm.

**Evidence.** G203 p29 §4.3.1, extracted verbatim this session:

> "The lines and level of any pipeline shall not deviate from that described in the contract
> by more than 20mm and combination of such deviation shall not create a reverse gradient."

`02` §2 carries this verbatim and marks the row ★ (verified against the source page
2026-08-17). `TUTORIALS/T02` §14: *"Line and level tolerance | 20 mm, and never a reverse
gradient"*. `GRADIENT_CRITERIA_VERIFIED.md` §3 quotes it verbatim. `08` is alone at 40 mm and
cites the same page for it.

**Why it is critical.** `02` §2 already works the consequence: at DN ≥ 900 the minimum
gradient is 0.75 mm/m, so 20 mm over a 120 m spacing eats about 22 % of the available fall.
Doubling the tolerance doubles the margin a flat trunk must carry — and that is exactly the
regime the 85 km main pipe runs in (DN1000 at 0.10 %).

**Fix.** `H10 | No reverse gradient; 20 mm line-and-level tolerance absorbed | G203-p29
§4.3.1`. If the intent was a 2 × 20 mm differential across a reach, say that in words and keep
20 mm as the cited value. A derived allowance must never be presented as the guideline's own.

---

### C2 — there is no minimum velocity in the hard set, and H5 substitutes the weaker of the two tests

**What is wrong.** H5 reads *"Self-cleansing: the steeper of Table 11 and the tractive-force
minimum | G203-p26–29"*. That is a rule about **gradient**. The guideline's requirement is
about **velocity**, and meeting H5 does not discharge it.

**Evidence.** G203 p26 §4.2.2.1, verbatim: *"the minimum velocity in the pipe shall be above
0.75 m/s at peak flow, with preferred velocity at 0.90 m/s."* `02` §1 carries it as its own
row; `T02` §14 lists it as its own constraint.

`GRADIENT_CRITERIA_VERIFIED.md` §2.1, tagged **[Certain]** after reproducing Table 11 from
Colebrook-White:

> "laying a pipe at its Table 11 gradient does **not** deliver 0.75 m/s at the design peak
> flow, because the pipe is not running full at peak — Table 10 caps it at d/D 0.65 or 0.50.
> Table 11 compliance and the p26 requirement of *"above 0.75 m/s at peak flow"* are two
> different tests, and **Table 11 is the weaker one**."

**Why it is critical.** A design satisfying all twelve hard constraints can still breach a
guideline "shall". The document's entire premise is that `02` says what is legal — yet the
ranking meant to make legality auditable has dropped the legality test itself. §10 has no
minimum-velocity row either.

**Fix.** Add `H5b | Velocity ≥ 0.75 m/s at peak flow, preferred 0.90 m/s | G203-p26 §4.2.2.1`,
and state in §6.2 that Table 11 is a full-bore derivation which does not by itself discharge
H5b. Add the §10 row. This decides a real design question: where the two disagree the pipe
gets steeper or smaller, never flatter.

---

### C3 — the 12 m cap is written in COVER; every number that justifies it was measured to INVERT

**What is wrong.** §5.1b layer 1: *"Cover reaches 12 m → station, mandatory"*. H4: *"Maximum
cover 12 m"*. §5.1c: *"12 → 14 m of cover"*. But §5.1's 239 breaches, the 226/13 split,
§5.1a's "breaches by 3 mm" and §5.1b's depth histogram were all measured on **depth to
invert**.

**Evidence.** `DEPTH_VS_PUMPING.md`'s own input table: `| d_max cover limit | 12.00 m to
invert | G203-p33, as coded |` — the label says cover, the value says invert. The same file
treats the two as different rules with different answers:

> "12 m to invert gives 219 breaches / 21 stations, 12 m *cover* gives 204 / 24, 10 m cover
> gives 275 / 16, 14 m cover gives 144 / 23"

Its coded tests are on depth (`depth_noPS[m] > d_max`; `DM = ∫(depth_noPS − depth_withPS) dL`).
`BREACH_DIAGNOSIS.md` computes `allowance = 12.00 − 1.30 − OD` — cover and outside diameter
are subtracted *from* the 12.00, so 12.00 is to invert. `W8_W10_POSTMORTEM.md` states it and
prices it: *"Both iterations have been stricter than the guideline by one outside diameter on
every reach — 0.30 m at DN200, 1.30 m at DN1200. Measured cost: 219 breaches to invert against
204 to cover."*

**Why it is critical, on three counts.**

1. **The unit does not match the evidence.** Restated as cover the station count moves the
   *opposite* way to intuition — 21 to 24 — because a looser per-reach cap changes which
   breaches consolidate. §5.1's 239 / 226 / 13 / 30-of-30 do not survive restatement
   unrecomputed, and §5.1c offers a thirteen-line list of invert breaches against a cover rule.
2. **It silently overturns settled doctrine.** `07_PROJECT_STATE.md` §2.3: *"Maximum depth is
   12 m, with no exceptions … The limit applies to every chamber AND to the trench between
   chambers."* That is depth. `08` changes it to cover — up to 1.3 m per reach — and records
   no supersession anywhere.
3. **It settles a question explicitly reserved for the user.** `W11a_BUILD_BRIEF.md`, "What
   needs your decision before stage 1", decision 3: *"The depth limit. Hard 12 m to invert, or
   10–12 m of cover as G203-p33 frames it? Cost of getting it wrong: 20 % of the pumping."*
   `T02` §15 lists the same item among the things the guideline does not decide: *"A single
   working figure, and whether it applies to cover or to invert."* `08` decides it, in the
   direction that relaxes the rule, without saying that it has.

**Fix.** State the measure once in bold at the head of §5 and refer to it everywhere else.
Record it as the answer to W11a decision 3 and as superseding PROJECT-STATE §2.3. Then either
re-run §5.1's table on the chosen measure or label every figure in §5.1–§5.1b "measured to
invert" with the cover-basis figures marked pending. Also state that 12 m is a project choice
inside G203's *"approximately 10 - 12m"* **recommendation** — H4 claims more authority than
the source grants (M1).

---

### C4 — §5.1b's depth-band table is not reproducible from its own cited source

**What is wrong.** §5.1b states: *"Allowed to dig through every breach, W10 would reach 12–14 m
at 132 breaches, 14–16 m at 63, 16–20 m at 27, 20–30 m at 11, and past 30 m at 6, the deepest
chamber at 57.9 m."* This table is the whole justification for the CAP being non-negotiable —
*"Beyond the cap the economics is arithmetic on air."*

**Evidence.** No depth-band distribution appears anywhere in `DEPTH_VS_PUMPING.md`. Its only
depth extremes are *"our design routinely lays pipe at 10–12 m — with 57 m as the extreme"* and
*"Our excursions run from 12 m to 57 m."* Recomputing the bands from that document's own cited
output `W10/run/research_breakeven_breaches.csv`, on `MAXDEPTH_NOPS` — the dig-through depth,
which is what "allowed to dig through every breach" describes — gives **114 / 53 / 39 / 24 / 9,
max 58.28 m**. On the as-solved `DEPTH_M` it gives 162 / 42 / 19 / 10 / 6, max 57.09 m. Neither
reproduces 132 / 63 / 27 / 11 / 6. **"57.9 m" matches nothing**: the two real extremes in the
corpus are 57.09 m (`BREACH_DIAGNOSIS.md`) and 58.28 m (the CSV).

**Why it is critical.** This is the load-bearing evidence for the one layer of the ladder that
may never be overridden, in a document whose §1 says the solver never grades its own homework.
A number that cannot be reproduced from the file it came from is not evidence.

**Fix.** Recompute from `research_breakeven_breaches.csv`, naming the column and the depth
measure, and cite the CSV. If the numbers came from an ad-hoc calculation the honest options
are to write the function that produces them or to delete the table — the cap still stands on
the sourced argument that no published rate table extends past about 5 m.

---

### C5 — about a dozen headline measurements cannot be traced to anything in the repository

**What is wrong.** The blockquote in §1 — the document's stated reason to exist — rests on five
numbers. Four cannot be found.

| Claim in `08` | Result of an exhaustive search of `W10/` and `_BRAIN/` (`.md`, `.py`, `.csv`, `.txt`) |
|---|---|
| §1, §3.3 "**4,041** dead-end fingers, **126 km**" | "4,041" occurs once in the corpus, as a **property count** in `WHAT_TO_SEWER.md`'s drop-branches-under-3.0-m³/d row. "126 km" occurs nowhere |
| §1, §3.6, §10 "**310** independent cycles / loops" | nowhere |
| §1 "**62 km** of pipe in wadis serving nothing" | nowhere. `CORRIDOR_QUALITY.md` §2, tagged [Certain], measures **136.1 km** of pipe on wadi ground and instructs *"Use 136.1 km as the pipe figure and say how it was measured"* |
| §1 "a trunk that carried a main on only **21 %** of its length" | nowhere. The only 21 % in the corpus is a **sub main's own length as a share of its catchment** (`HIERARCHY_RULES.md` R4) — a different quantity |
| §3.4 "**2,372°** of direction change … one reach turning **165°**" | nowhere |
| §4.4 "a laid gradient of **980 %**" and "**43 reaches** over the 3.0 m/s maximum" | nowhere |
| §3.2 "W10 achieved **76 m** with **3.5 junctions per km**" | nowhere for W10. The nearest real figures are W7's 105 m and 3.6 junctions/km (`07_PROJECT_STATE.md`) and W10's 11.1 nodes/km (`W11a_BUILD_BRIEF.md` P4) |

**Why it is critical.** `00_INDEX.md` prime rule 1: *"No invented metrics."*
`W11a_BUILD_BRIEF.md` P2: *"Every published number comes from exactly one function … seven
different lifting-station counts are in circulation."* `08` is the document meant to enforce
both, and it breaks them in its opening paragraph. A reader trying to verify the case against
W10 — which is the case for changing method — cannot.

**Fix.** For each: name the function or CSV that produced it, or delete it. Where a researched
figure already exists, use it — the wadi number is 136.1 km on the pipe, and it is a far
stronger fact than 62 km.

---

### C6 — the tier vocabulary contradicts the guideline, `02` and T02, and it disables H8 and three §10 checks

**What is wrong.** §3.1 defines the hierarchy as *"Properties feed riders, riders feed
laterals, laterals chain into laterals, laterals join a sub main, sub mains join the trunk"*,
with a lateral zone of median 132 m and cap 920 m. That is not the guideline's hierarchy, and
`08` never says so.

**Evidence — G203's own vocabulary, extracted this session.** p17 §3.2 sets the chain PCC →
PC Sewer → HCC → (sometimes) Rider Sewers → **Lateral Sewer** → **Main Sewer**, and states
verbatim: *"Rider Sewers and Lateral Sewers (maximum Length 45 m) are forming the Tertiary
Sewage Network … while the Main Sewer is part of the Secondary Sewage Network."* p21: the
secondary network *"includes the headers or main sewers usually laid under the streets"*.
p22 Table 6: **Lateral Sewer, Maximum Length 45 m, OD 200 mm (minimal)**. p18 Table 5:
**Lateral Sewer, gradient minimal 1 %, maximal 10 %**.

`TUTORIALS/T02` §5, the project's own page-cited reference: *"Properties feed riders, riders
feed laterals, **laterals feed main sewers**, and only the collectors reach the trunk."*

`02` §2: *"Tertiary slopes are separate and much steeper (p18 Tab 5): property connection
sewer min 3 % / max 10 %; rider sewer min 1 % / max 10 %; lateral sewer min 1 % / max 10 %.
Table 11 above applies to the secondary network — **using its 0.5 % at DN200 for a lateral is
a design trap.**"*

So `08`'s "lateral" is G203's **main sewer**, wearing the name G203 caps at 45 m and `02`
requires at ≥ 1 %. `08` has no main-sewer tier at all and adds a "sub main" that exists in
NAMA's manhole IDs but in no guideline.

**Why it is critical — three concrete consequences.**

1. **H8 cannot be applied.** *"Minimum sizes and materials by tier | G203-p22 Tab 6"* — Tab 6
   is keyed to G203's tier names. With the names redefined and no mapping published, the
   constraint has no determinate meaning. It is also incomplete: trunk material above 600 mm
   is Table 14 on p35, not Table 6.
2. **Three §10 checks are untestable.** *"Tier populated; tier monotonic downstream"* has no
   defined tier set. *"The given trunk carries a **main diameter** over its whole length"* —
   "main diameter" is undefined, and read against Table 6 a "main sewer" is OD200–300, so a
   DN200 trunk would pass a check written to catch exactly that failure.
3. **The gradient basis for 1,883 km is left open.** If `08`-laterals are G203-laterals, `02`
   says they take 1 % minimum, not Table 11's 0.5 % at DN200 — and `02` calls the alternative
   a design trap by name. That single ambiguity moves every invert in the network.

**Fix.** Put a five-row mapping table at the head of §3 — *our name | G203 name | G203 rules
that attach | NAMA token*. State explicitly that Table 5's 1 % and Table 6's 45 m bind the
tertiary elements as G203 defines them, and that the street-run tier is a **main sewer**
governed by Table 11. Rename "lateral zone", or adopt the guideline's name — but not both
meanings at once.

---

### C7 — the §10 audit registry does not test what made W10 non-issuable, nor five of the twelve hard constraints

**What is wrong.** §10 opens *"Each rule above has a check in the audit registry."* It does not.

W10 was audited non-compliant on four counts (`W10_SUMMARY.md`, `W11a_BUILD_BRIEF.md` P1):
45.92 km below minimum cover; 2.80 km of surcharged trunk; 10.68 km over the d/D limit;
1.67 km of pipe along a dual carriageway. **None of the four has a row in §10.**

| | Constraint | Row in §10? |
|---|---|---|
| H1 | no pipe along a dual carriageway; none in a wadi | **no** |
| H2 | capacity ≥ discharge within the d/D limit | **no** |
| H3 | minimum cover 1.30 m on the reach's own OD | **no** — W10's single largest failure |
| H4 | maximum cover 12 m | **no** (only the rounding-attributable stations and the derogation list) |
| H10 | no reverse gradient; tolerance absorbed | **no** |
| H11 | chamber spacing within Table 12 | **no** — §10's 3.2 row reports a *median* |

Also absent: §3.5 (which says it "is checked and corrected in the review pass" — a pass is not
a test); §6.3's start-year self-cleansing check; and any check that depth is measured
**between** chambers as well as at them, which `07_PROJECT_STATE.md` §2.3 requires,
`W11a_BUILD_BRIEF.md` invariant 5 requires, and `T02` §16 states outright: *"A rule about cover
must be checked along the whole pipe, not only at the two manholes: ground rises between
chambers, and the shallowest point is rarely at either end."*

**And the one row that addresses W10's headline defect would have passed it.** §10's 3.2 check
is *"Median run length reported against the as-built's 88 m"*. W10's median was fine — its
defect was a **maximum of 6,541 m** and **4,763 reaches breaching Table 12, 1,220 km, 65 % of
the length** (`DELIVERABLE_SPEC.md` row 8). A median cannot see a tail.

**Fix.** One row per hard constraint H1–H12, plus §6.3's start-year check, plus a mid-reach
cover check. Change 3.2 to *"no reach exceeds Table 12; report the maximum and the count of
exceedances"*. Cross-reference the 59-check contract in `W8_W10_POSTMORTEM.md` rather than
maintaining a second, shorter list that omits half of it.

---

### C8 — §9's knowledge-base citations and named-staff quotations are absent from the sources it names, and are used to overturn caveats and to justify §4.4

**What is wrong.** §9 names `SEWERGEMS_DESIGN_METHOD.md` and `DESIGN_ENGINES_COMPARED.md` as
its *"Full account and citations"*. Searching both files for `KB00`, `Dringoli`, `Choure` and
`Kampa` returns **zero hits**. Not one of the six KB numbers or five named-staff quotations in
§9.3–§9.3d exists in either source.

| `08` §9 asserts | In the cited sources |
|---|---|
| KB0016752: *"The design solver runs a check in both directions, so it is designed both ways."* | **not found**; no such KB, no such sentence |
| KB0016766 carrying the reverse pass verbatim | the sentence **is** in the sources, attributed to Bentley's **Design Priorities help page**, not to a KB |
| Jesse Dringoli: *"minimum cover is higher priority than minimum slope, and maximum cover is below everything…"* | **not found**, and partly contradicted — minimum slope is not in the ladder at all (*"Acted on, unranked"*), and maximum cover **outranks** tractive stress |
| Dringoli: *"Automated design is not meant to provide perfect results."* | **not found**. The real vendor sentence is *"As with any automated design, the program's design is intended only as a preliminary step… The modeler should always review any automated design"* |
| §9.3a: `Allow Drop Structure` fires *"when manhole upstream pipe slope exceeds the conduit maximum slope"*; `Use Drop Structure to Minimize Cover`; `Minimum Drop Depth`; KB0015543, KB0057310 | **not found — and directly contradicted.** The source says: *"The **trigger condition** for inserting a drop. Nothing says 'when slope exceeds X' … **Cannot tell.**"* and *"What triggers a drop structure, how its height is chosen, whether a maximum drop exists — **Not documented anywhere.**"* |
| §9.3b Sushma Choure on pumping stations; KB0016750 | **not found**. The underlying point is well supported without them (the design dialogs contain only Gravity Pipe, Node and Inlet) |
| §9.3c Dringoli and Choure on steady state; GVF-Convex "(Kampa)" | **not found**. Steady state is supported from the help pages; the source explicitly warns against the GVF-Convex assertion |
| §9.3d KB0057316 on sizing from the upstream-end flow before attenuation | **not found**. Zero hits for "attenuation" in either file; the claim has no basis in the cited sources |

The source file states plainly why: *"Bentley Communities forum threads and the Bentley/Virtuosity
blog are JavaScript-rendered and could not be read directly; none of the claims above depends
on them."*

**Why it is critical — the unverifiable citations do work in the document.**

1. **§9.3 uses KB0016752 to withdraw a caveat the source insists on.** *"The earlier caveat is
   withdrawn. A follow-up sweep of Bentley's knowledge base settled it."* The source's caveat
   is emphatic: the 22 steps and the reverse pass *"sit under the heading 'Design Steps When
   Conduit Flow Travel Time Is Considered (**StormCAD Only**)'"*, *"**Cannot tell** whether the
   sanitary (GVF-Convex) path executes exactly these 22 steps"*, and — in bold in the source —
   ***"Do not write 'SewerGEMS performs 22 steps' into a client document."***
2. **§9.4 retracts a finding its own sources make.** *"An earlier draft called the method a
   'greedy downstream sweep'. **That is wrong for Bentley and must not be written down**."* The
   source says *"**Reach-by-reach, sequential, and greedy.**"*, and the second source makes
   "greedy downstream sweep" its [Certain] convergent finding across four vendors. The
   retraction rests solely on KB0016752, which is in neither file.
3. **§9.3a is cited as *"direct vendor support for §4.4"*** — our own drop-chamber rule — on a
   trigger and two field names the source records as **"Cannot tell"** and **"Not documented
   anywhere"**. A design rule of ours is being justified by vendor behaviour that the research
   could not establish.
4. **§9.4's *"no vendor claims anywhere to minimise network cost"*** is contradicted by the
   source's own InfoSewer line: *"InfoSewer designs existing pipes considering flow capacity
   constraints while minimizing cost."*

**Fairness.** It is possible a later web sweep found these articles and was never written into
the research files. If so, the sweep must be written up before the claims can stand — as they
are, six KB numbers, five attributed quotations and two retractions cannot be checked by
anyone, in the section of the document that most loudly presents itself as verified.

**Fix.** Either (a) add the sweep to `SEWERGEMS_DESIGN_METHOD.md` with URLs and retrieval dates
and reconcile it with the caveats it overturns, or (b) strip §9 back to what the two research
files actually support: the eight-level ladder (verbatim, order exact), the demotion of maximum
cover and maximum velocity, the forward/reverse pass structure from the help pages with its
StormCAD-scope caveat intact, "only gravity elements are designed" from the dialog contents,
and the four literature findings in §9.5. Restore "greedy" and drop §9.3d entirely.

---

## MAJOR

### M1 — H4 says "no exemption"; §5.1c is an exemption

§6a H4: *"Maximum cover 12 m — the cap … **no exemption**"*. §5.1c: *"**The single bounded
derogation** — the only thing that can REMOVE a station."* Both are binding, one page apart,
and the document never says which governs.

It also collides with the project's standing rule against exempted checks. `T02` §16: *"Never
let a check carry an exemption. The moment a check is allowed to skip an element … the rule is
gone, and the result reads as a pass. If a design genuinely cannot meet a rule, the honest
outcome is a **recorded failure with a reason**, not a silent exclusion."*

**Fix.** H4 → *"Maximum cover 12 m. No relaxation. A §5.1c derogation is recorded as a
**non-compliance accepted by NWS**, never as a pass."* Mirror that in §10's 5.1c row.
Separately, H4's authority is overstated: G203-p33 is *"The **recommended** maximum cover …
is approximately 10 - 12m"*, and 12 is our choice inside a range. Say so.

### M2 — §5's opening sentence contradicts §5.1b layer 1

§5 opens *"**A depth limit is not a reason to pump. Excavation cost is.**"* §5.1b layer 1:
*"Cover reaches 12 m → station, mandatory | **No.** Not by cost, not by anything."* Opposite
rules for the same decision, both stated as binding, both in §5. §5.1b is dated 2026-09-02 and
attributed to a user instruction, so it presumably wins — but a binding source must not require
the reader to date-order its own paragraphs.

**Fix.** *"The guideline's stated trigger is excavation cost, not depth (G203-p33). We impose a
cap above it, for the reasons in §5.1b."*

### M3 — §5.3 adds a fourth reason for a station that neither the ladder nor its own check can express

§5.3: *"A station that makes a package independently buildable earns its place **even when the
trench would have been cheaper**. This is the one case where objective 4 outranks objective 5."*
§5.1b has three layers. §10's check: *"Every station attributed to its layer — cap, veto or
economics."* A commissioning station is none of the three and fails its own audit row.

**Fix.** Add a fourth attribution — COMMISSIONING — to §5.1b and to the §10 row, with the test
it must pass: it creates a package seam, and the package downstream of it is one connected tree
with one outlet.

### M4 — §9.2 says "ADOPT the artefact", then drops Bentley's two highest-priority constraints

The ranking §9.2 reproduces is headed by **1 pipe fits within adjacent EXISTING structures** and
**2 pipe crown not above an adjacent DESIGNED structure**. Neither has any counterpart in H1–H12.

This project is full of fixed points: the existing works, whose inlet invert is **GAP-7** and is
currently the screening assumption *"ground level −(2–4 m)"*; the built 101.1 km gravity network
and the only built 10.0 km force main; the given `Main Pipe.shp`; and W11 is explicitly the
brownfield run. `08` contains **no rule for tying into an existing asset and no rule for the
outfall boundary level** — the single most load-bearing input to §2 stage 3, the stage the
document calls its most important line.

**Fix.** Add `H0 | The design fits its fixed points — existing works inlet, existing manholes and
rising mains, the given Main Pipe tie-in. Every fixed level is stated with its source or its GAP
number | G203-p33 §4.6.1; Bentley priorities 1–2`. Require the outfall level to be declared
before the trunk is levelled.

### M5 — backdrops, the 600 mm trigger and vortex shafts are absent, replaced by a foreign detail

§4.4 is the steep-ground section. It cites Water UK DCG B5.2.27 for *"ramped, not vertical"* and
Ten States for a *"drop at ≥ 610 mm"*, and says nothing about the governing rules — all of which
are already in `02` §5 and `T02` §14. G203 p30, verbatim:

> "Connections under these conditions require the use of a backdrop when the difference in invert
> elevations exceeds 600 mm. Backdrops shall be constructed external to the manhole … Internal
> backdrops are not permitted on manholes that are less than 1.5 m in diameter … The maximum
> backdrop height should be of 2 m. Beyond this limit, specific devices like vortex drop shafts
> should be used."

(p19 §3.6 states the 600 mm rule a second time.) `HIERARCHY_RULES.md` step 6 makes it a required
check — *"drops ≥ 2.00 m needing a vortex shaft — report and price every one; as-built 37"* — and
`W11a_BUILD_BRIEF.md` P10 records that 37 as-built backdrops already breach it. On a scheme with a
closed western basin and an 11.93 m saddle, 2 m drops will not be rare.

**Fix.** State G203's numbers first; keep the foreign standards only where G203 is silent. Add two
§10 rows: backdrops ≥ 0.60 m as a share of connections (report), and drops ≥ 2.00 m requiring a
vortex shaft (report and price every one).

### M6 — rising mains are inside the stated scope and have almost no philosophy

§Scope: *"the gravity foul sewer network, from the property connection to the works inlet,
**including its lifting stations and rising mains**."* The document then gives rising mains one
line — H6's 2.5 m/s — and never says which of H1–H12 apply to a pressure pipe. `T02` §11 is
explicit that most do not: *"The rising main: Runs FULL and under pressure. **Gradient, d/D and
cover-to-fall rules do not apply to it.**"* So H2, H5 and H11 as written are wrong for a rising
main, and `08` does not say so.

Missing, all in `02` §8 or `T02` §11:

- minimum velocity **0.75 m/s continuous, 1.0 intermittent, 1.2 vertical**, and the binding detail
  that it applies at the **Table 16 minimum flow**, not the average. `07_PROJECT_STATE.md` records
  **17 of 25 W10 rising mains below 0.75 m/s** — a live defect that no rule in `08` would catch
- sized on **pump duty**, not on the arriving gravity flow (`T02` §11; PROJECT-STATE §2.3)
- **retention time ideally ≤ 30 min** (G203-p50) — the septicity limit for pressure pipe, which
  §6.3a discusses only for gravity
- run full and remain full at all times (p51); termination **not more than 300 mm above the
  receiving manhole flow line** (p55); gradients 1:500 rising / 1:300 falling, never below 1:750
  (p50); wadi-crossing cover 1.5 m (p52) and 2.0 m in soft soil (G1-p86)

**Fix.** A §5.4 "the rising main and the station" carrying those rules, and one sentence in §6a
stating which hard constraints do not apply to pressure pipe.

### M7 — a G203 "must" is demoted to the lowest preference

G203 p29 §4.3.1, verbatim: *"**Uniform slopes must be maintained between successive manholes.**"*
`02` §2 and `T02` §14 both carry it as a requirement. `08` puts it in **P1**, the preference tier
that *"yields to any hard constraint"* — while §4.2 states the same rule as a requirement. The
document contradicts itself and the wrong version reached the ranking.

**Fix.** Split it. **Hard:** uniform gradient between successive chambers (G203-p29).
**Preference P1:** the round 0.05 % step, which is ours and does yield.

### M8 — the tractive-force minimum is invoked with no τ and no mention of GAP-9

H5 and §6.2 both rest on *"the steeper of Table 11 and the tractive-force minimum"*.
`GRADIENT_CRITERIA_VERIFIED.md` §3.1, **[Certain]**: *"PAM-GUD-203 gives no numeric value for tau
anywhere"*, and G201 has no tractive method at all. `05_GAPS.md` GAP-9 adopts τ = 1 Pa as a
project assumption that *"must keep being declared as one in every deliverable"*, and W4 measured
**1,626 pipes exposed if τ = 2**. `T02` §15 lists τ first among the things the guideline does not
decide. As written H5 cannot be executed, and it presents a project assumption as a guideline
constraint. `08` references no GAP anywhere in 636 lines.

**Fix.** In §6.2: *"τ = 1 Pa [GAP-9], with the formula's own derivation condition d/D = 0.2,
n = 0.013 (G203-p27). The τ = 2 sensitivity is reported on every deliverable."*

### M9 — the evidence in §5.1, §8 and §9.5 is stated more strongly than its sources

| # | `08` says | The source says |
|---|---|---|
| a | §5.1: "Of those 13, **10** cheaper to dig through than to pump" | 10 is **conditional on the manning rule**. Without manning it is **2 of 13** |
| b | §5.1: "30 of 30 … at every rate and **every cost exponent**" | *"Stations kept: 30 of 30 … at every **rate tested**"*. The exponent is a separate grid |
| c | §8.1: "**NWS's own pre-investment appraisals price station establishment at 169,127 OMR** of present value per station" | NWS's figure is **1,000 OMR/month**. 169,127 is *this project's* 25-year PV of it (PVAF 14.0939 × 12,000). Attributing our arithmetic to NWS matters exactly here, because the same paragraph's instruction is to settle that number **with** NWS |
| d | §8.2: EPA-430/9-81-003, "777 projects; … rises **2.7× to 17×** above 15 ft" | tagged **[Likely]**: *"extracted by the fetcher from the NEPIS OCR text and I could not pull the raw text a second way to re-verify them digit by digit"* |
| e | §8.2: the three depth exponents 1.0 / 1.47–1.53 / 2.0 | quotations [Certain], but the source adds **[Likely] on which is right for Ibri: "none of them, until the BoQs arrive"** |
| f | §5.1: "Re-measured correctly (independent rebuild reproducing all 239 lift heights to 0.005 m)" | the 226/13 split carries **[Likely]**, because the script producing `recover_m` could not be read |
| g | §8.2: "**6–10 m** (the depth limit the optimisation literature actually imposes)" | tagged **[Likely]** and stated as **5 to 10 m** |
| h | §9.5: "**Li & Matthew (1990)** … relaxing the maximum depth constraint reduces the station count" | Li & Matthew supply the *balance* finding only. The relaxation finding is **Duque et al. (2024)**. The source also records *"I have not read Li & Matthew in the original"* — [Likely] |
| i | §9.5: "10 m cover gives 16 stations but 3,095 m of lift, 14 m gives 2,247 m" | not in either §8 or §9 source. It is in `W10/docs/OPTIMISATION.md` — and those runs were solved to **invert**, so "cover" is wrong there too (C3) |
| j | §9.1: "[**Certain**, four independent vendors] not one of them chooses a layout" | the InfoWorks ICM cell of that table is tagged **[Likely]** in the source, from a search index because the page refused a direct fetch |
| k | §9.4: InfoDrainage "**no reverse pass**" | the source refuses that phrasing: *"I will not claim InfoDrainage has no reverse pass — I will say Innovyze does not document one."* |
| l | §9.3: the reverse pass as "reconciliation, not re-optimisation" | tagged **[Likely]** in the source; stated flat in `08` |

There is also a breach-count instability inherited without naming: the corpus carries **204, 219,
220 and 239** breaches depending on measure and run. `08` uses 239 throughout and never says
which definition produced it.

**Fix.** Restore the dropped tags, add the two conditions (a, b), correct the two attributions
(c, h), cite `OPTIMISATION.md` for (i), soften (j)–(l) to the source's own wording, and state the
breach definition once.

### M10 — three confidence tags in 636 lines, all [Certain], all in §9

§Status claims *"every claim carries where it came from"*. In practice §§1–8, 10 and 11 carry no
confidence tag at all, while §8 is built almost entirely on extrapolated and OCR-sourced data the
source file itself tags [Likely]. This is also a standing user instruction.

**Fix.** Tag at minimum: §3.1's sub-main spacing rule ([Likely] in `HIERARCHY_RULES.md` R5),
§5.1's split, §5.1b's histogram once recomputed, §8.2's rate tables, §8.3's scaling law, and
§6.3a's causal claim that septicity is *the reason* p29 exists — an inference, not a stated link.

### M11 — chamber spacing: the governing table is not quoted, and a run is confused with a spacing

§3.2 cites Water UK DCG's 90 m and Ten States' *"120 m for ≤375 mm and 150 m for 450–750 mm"*.
G203-p30 Table 12 — which is what binds — appears only as a one-line reference in H11. Two
problems follow.

1. **Following §3.2's cited standards can breach `02`.** Ten States allows 120 m up to 15 in
   (375 mm); Table 12 allows **100 m** for DN200–315. Table 12 also carries a mechanism `08`
   never mentions: *"Any alteration in the above specified spacing of manholes, consultant has to
   obtain pre-approval from NWS."* (The source also shows §3.2's conversion is silent: the Ten
   States figures are in inches, and its 185 m allowance "with adequate modern cleaning
   equipment" is dropped.)
2. **"Target the as-built's median run of 88 m" mixes three different measurements.** 88 m is
   W8's median *lateral length*; the as-built's median *chamber spacing* is **29.2 m** and its
   median lateral *zone* length is **132 m** (`HIERARCHY_RULES.md` R2, which §3.1 quotes on the
   same page). A run is not a spacing — and `HIERARCHY_RULES.md` lists 30 m chamber spacing under
   *"What NOT to carry over"*.

**Fix.** Lead §3.2 with Table 12 and the NWS pre-approval mechanism; keep DCG and Ten States as
corroboration that the cap is an operations rule. State the design target as a **maximum** against
Table 12 and give the run-length target its own name.

### M12 — the hierarchy research's operating rules are omitted, including the number that sizes the whole job

§3.1 takes four rules from `HIERARCHY_RULES.md` and leaves the rest of a six-step recipe behind.
Missing, all measured and all checkable:

- **~270 km of sub main that does not exist today** — the largest quantitative consequence of the
  whole research (`HIERARCHY_RULES.md` §Guard; `W11a_BUILD_BRIEF.md` P5). `08` never states the
  size of the work it is commissioning
- the tier-share pass bands — trunk **10–15 %**, sub main **12–18 %**, lateral **68–76 %** of
  length. `W11a_BUILD_BRIEF.md` makes these a **build gate**
- **"a district under about 4 km of sewer gets no sub main"** (R6). §3.1 says a sub main is *not*
  defined by a load threshold but supplies no positive rule for when one is created
- **"Only sub mains touch the trunk"**, expected at one trunk connection per 4–5 km of network —
  of the order of 400 on 1,883 km. This is the direct successor to W8's founding lesson, and it
  is absent
- the lateral ceiling: no lateral pipe carries more than **136 properties or 2,467 m** of
  contributing sewer (R3)
- the two checks the as-built **fails** and W11a must not inherit: **no main sewer below DN200**,
  and **no pipe flatter than the governing minimum gradient** (65.5 % of as-built sub mains are)
- the trunk-alignment tie-break: *"prefer the route that minimises ground level − local median
  over 300 m"*

**Fix.** Fold the six-step recipe and its pass bands into §3.1, put the pass bands in §10, and
state the 270 km.

### M13 — "everything belongs in the public corridor" is missing, and stage 2 has no corridor rules beyond wadi and dual

§2 stage 2 is *"the corridors, with their provenance"*, and the only rules given are the wadi and
dual-carriageway exclusions. `T02` §12 lists what actually binds a corridor and `08` carries none
of it:

- **private land** — *"A chamber or pipe inside a plot is a wayleave problem for the life of the
  asset. Everything belongs in the public corridor."* Live: 22 chambers cannot be freed from a
  plot; `auto_link` runs **22.9 % through plots**; `auto_block` fronts plots of which not one is
  built (`CORRIDOR_QUALITY.md`)
- **minimum horizontal clearance 3 m to other utilities** (G203-p33) — the only third-party
  utility rule in the guideline, and it is nowhere in `08`
- **service reservation width by diameter** (G203-p32 Table 13 / p35 Table 15) — 2.00 m at
  DN200–500 rising to 4.40 m; it decides whether a corridor can physically hold the pipe
- **trenchless crossings as a counted cost driver**, and existing underpasses as free crossings
- **corridor provenance carried to the pipe** — `W11a` P6 requires `SRC` and `CONFIDENCE` on every
  pipe through to the drawings. §2 says "with their provenance" and never says what that means or
  that it must survive to the deliverable

There is also an unresolved collision: H1 forbids any pipe along a dual carriageway, and **236
plots have no other frontage**. §6a's resolution menu — station, drop chamber, re-route — cannot
solve it, and the document should name it as a user decision, as `W11a` does.

**Fix.** Give stage 2 the five rules above; add a §10 row for chambers and pipes inside registered
plots (target zero, exceptions named); name the 236-plot case as an open decision.

### M14 — ventilation is a guideline "shall" with numbers, and it is in neither `02` nor `08`

G203 §4.5 "Air vents on gravity network", p31–32, verbatim: *"The design of the vent **shall** be
adapted to the urban area and the surroundings but **shall not be less than 150mm and 6m above
ground** and equipped with a cap made of UV resisting material."* Plus p19 §3.7: property vents
extended 1 m above the roof.

§6.3a makes septicity a design driver and never mentions the guideline's own ventilation
requirement for the gravity network. `02` §12d covers odour and H₂S but has no vent row.

**Fix.** Add the vent rule to `02` §5 — it is a criterion, not a philosophy — and give §6.3a a
clause requiring vent locations to be part of the septicity answer rather than an add-on.

---

## MINOR

| # | § | Finding | Fix |
|---|---|---|---|
| m1 | §10 | Two rows are labelled **3.8**. The 10 m branch-clearance rule is §3.9 | renumber |
| m2 | §10 | No row for §3.5 at all; §3.5 says it "is checked and corrected in the review pass" — a pass is not a test | add a check, or say plainly it is judgement with no automated test |
| m3 | §3.5 | **"Through-street" is undefined.** The road layer carries `StrCls` 01–05, and `HIERARCHY_RULES.md` step 4 already says *"running on the highest street class available"* | define it as a `StrCls` threshold |
| m4 | §3.3 | **"a dead-end reach under ~60 m serving nothing"** — 60 m in this project is `PLOT_SERVED_M`, a plot-proximity radius, not a reach length. The rule needs a length test *and* a load test, and the load test already exists: no load-bearing plot within 60 m **and** under 1 m³/d (`WHAT_TO_SEWER.md`) | restate with both tests and their sources |
| m5 | §5.1b | **"Unmaintainable" has no test and no decider.** G203-p33 supplies a basis and is not cited: *"Location of Sewerage and pipelines shall allow adequate (24 hours per day x 7 days per week) access"* | cite p33; make the three named cases a closed set; require any addition to be signed |
| m6 | §5.1c | **"it is short, and the length is stated"** — no number, in a clause whose other four conditions are all quantified | state a length, or say the length is reported and NWS decides |
| m7 | §3.10 | The rider's "up to **3** property connections" is cited to *"G203-p19 3.4"*. It is on **p17 §3.2** and reads *"Several HCC (**usually** up to 3)"* — a norm, not a limit. p19 §3.4 is the stubs / plugged-ports rule, which the stub-out bullet does not cite | swap the citations; soften "up to 3" to the guideline's wording |
| m8 | §3.10 | Gives the property connection's 3–10 % but **omits the rider and lateral 1–10 %** (G203-p18 Table 5, in `02` §2). States 50 m as a maximum where p18 says *"should not exceed 50 m"* | add the rider/lateral band; keep 50 m but mark it a recommendation applied as a limit |
| m9 | §6a H3 | Omits G203-p33's own relief: *"If circumstances require installation of a pipe with depth less than 1.3 m above the crown, then concrete protection is required. The minimum cover above the pipe and its protection shall be 0.5 m"* — a legal tool the design is currently denied | add it as a stated exception with its condition |
| m10 | §2 / §7 | §2: *"Each stage is fixed before the next begins."* §7's pass 2 moves sub mains and re-sites stations after stage 6, and §6a resolves hard-constraint conflicts by "re-route", which undoes stage 2 | say pass 2 is the sanctioned way back and any other return is a recorded decision |
| m11 | §11 | States the built network as "3,266 pipes, **101.1 km**". Correct (`EXISTING_NETWORK.md`: 111.567 km as catalogued, **101.098 km** true gravity) — but `README.md`, `CLAUDE.md` and `07_PROJECT_STATE.md` all still say 111.6 km | fix the three live documents, not `08` |
| m12 | §6.4 | "110 of their pipes cannot pass today's peak flow" is right, but `HIERARCHY_RULES.md` lists as open *"whether any of the 110 surcharging pipes actually surcharge — no flow monitoring, no condition grading, connection status unknown"* | carry the caveat |
| m13 | §6.3 | "Size on the ultimate horizon, check on the first year" names two horizons. The scope requires **four** model years — start / 2030 / 2055 / ultimate (`02` §11.6; `DELIVERABLE_SPEC.md`) — and §2 stage 7 gives no rule tying packages to them | name the four; say which sizes and which checks |
| m14 | §6.3a | Retention time is *"a design output, reported per route"* with no threshold. G203-p185 Table 99 (Fayoux) supplies one and is already in `02` §12d | score routes on Fayoux; flag anything scoring "significant" |
| m15 | — | **Chamber types and sizes** are in the guideline (p19 §3.4: rectangular 600 × 750 mm to 1.4 m, not under traffic lanes; circular 1.0 m internal, 1.0–2.0 m deep) and in `DELIVERABLE_SPEC.md`, but in neither `02` nor `08` | add to `02` §5 |
| m16 | — | **Backflow prevention** (boundary trap, backwater valve, BS EN 13564-1:2002 — G203 p19–20) and **adoption testing** (BS EN 1610 before transfer to NWS — p33 §4.7) appear nowhere, and §1 objective 3 is "it can be operated and adopted" | add to `02` |
| m17 | — | **Flow monitoring / calibration**: `02` §12e carries the binding acceptance band (G1-p145 Table 32 — peak flow ±10–15 %, volume ±15 %, pump runtime ±10 %), unachievable without monitoring data. §7's three passes have no place for calibration | one line in §7 |
| m18 | §8 | **Ground conditions have no term at all.** Every rate cited is for unspecified ground; `02` §12 carries the geotechnical basis (boreholes to 5.0 m below invert, p199; spacing G1-p40–41 Table 7). Rock or high groundwater would move excavation cost more than the depth exponent the section spends most of its length on | one sentence naming it as the largest unquantified term |
| m19 | §8.3 | The Cabral intercept is quoted as **4.3189** in `08` and in one line of the source, and coded as **4.3184** in three other lines of the same source | settle it |
| m20 | §9.2 | *"Verbatim, identical in SewerCAD and SewerGEMS"* overstates: the source says the two help pages differ by two words and only *"the eight priorities, the 22-step sequence and the reverse pass are byte-identical"* | narrow the claim to the ladder |

**On the retraction (asked specifically).** §5.1's retraction is handled well and is one of the
best things in the document: the wrong claim is named, the mechanism is given
(`d = min(d, MIN_COVER_CROWN + od)`), and the wrong physics is stated outright. **Nothing
downstream relies on the retracted claim** — §5.2 keeps only the method, §5.1c uses the corrected
13, and §8.4 correctly requires a re-breach to *defer* rather than save a station. The one residue
is the count itself: 239 is one of four figures in circulation (C3, M9).

---

## Answers to the six questions asked

**A — contradictions with `02` and the guidelines.** Four outright: C1 (40 mm vs 20 mm), C2 (no
minimum velocity), C6 (tier vocabulary vs Tables 5 and 6), M7 (a "must" demoted to a preference).
Two partial: M5 (backdrop rules replaced by foreign ones), m9 (the concrete-protection relief
dropped). Everything else checked — 3.0 and 2.5 m/s, Table 11, Table 12, minimum cover 1.30 m,
inlet angle 90°, property connection 3–10 % and 50 m, OD160, 0.60 m cover, the p29 oversizing
prohibition, the trunk-main definition — is **correct against the source pages**, which were
re-extracted for this review.

**B — internal consistency of the four orderings.** They are not reconciled. Three concrete
situations, as asked:

1. *A chamber at 12.0 m on a reach that demonstrably rejoins 400 m later.* §6a H4 says no
   exemption; §5.1c says dig through if it rejoins, peaks under 14 m and NWS accepts. The
   document does not say which wins. **Unresolved (M1).**
2. *A station that is needed on neither cost nor depth, but makes a 20 km package commissionable.*
   §5.1b has no layer for it; §5.3 says build it; §10 requires it to be attributed to cap, veto or
   economics, so it fails its own audit. **Unresolved (M3).**
3. *Two hard constraints collide and the resolution offered is "re-route".* §6a permits it; §2
   says each stage is fixed before the next begins and a re-route undoes stage 2; §7's pass 2 does
   exactly this and is called mandatory. **Unresolved (m10).**

A fourth, structural: §1 ranks compliance first, yet §3.8 accommodates the H9 90° "shall" by
flagging exceptions and §5.1c accommodates H4 by derogation. Objective 1 is in practice a
"comply-or-name-it" rule, and the document never says so.

**C — unimplementable as written.** H5 without a τ (M8); H8 without a tier mapping (C6);
"through-street" (m3); "no fingers" measured how (m4); "unmaintainable" (m5); "short excursion"
(m6); "main diameter" in §10's trunk check (C6); "tier monotonic downstream" with no tier set
(C6); "retention time reported" with no threshold (m14); §3.2's target, which mixes a run with a
spacing (M11).

**D — missing.** Ranked by how much each would change the design: the sub-main sizing rules and
the 270 km (M12); rising mains (M6); existing-asset interfaces and the outfall level (M4);
corridor rules beyond wadi and dual (M13); backdrops and vortex shafts (M5); ventilation (M14);
the four horizons and the start-year check (m13, C7); Fayoux thresholds for septicity (m14);
chamber types (m15); adoption testing and backflow prevention (m16); calibration and flow
monitoring (m17); ground conditions (m18). Checked and **adequately covered elsewhere**:
surcharge and the hydraulic grade line (H2's d/D limit is the operative rule, and G203 sets no
HGL criterion — "grade line" occurs once, in the Manning definition); groundwater and buoyancy
(G203 is silent for gravity sewers; `02` §12 carries the geotechnical requirement and `02` §11b
the anti-flotation check at wadi crossings); trenchless crossings (`02` §6, though not in `08` —
M13).

**E — evidence honesty.** Six unverifiable KB citations and five unverifiable attributed
quotations (C8), a dozen untraceable measurements (C5), one unreproducible table (C4), one unit
mismatch between rule and evidence (C3), twelve over-claims and misattributions (M9), and three
confidence tags in 636 lines (M10). Against that: the §5.1 retraction is exemplary, §3.3 and §9.2
volunteer their own weaknesses (*"this rule is OURS, not a standard"*; *"stated honestly because
it will be challenged"*), and the eight-level ladder, the demotions, the pass structure and the
§9.5 literature all check out against the sources. The document is honest in intent and unreliable
in execution.

**F — usability.** Navigable and well written; the priority tables are the right artefact. Three
structural problems. (i) **§9 is about 110 lines of vendor research inside a philosophy document**
— four sentences of it change our method (no engine picks a layout; the reverse pass is a cheap
reconciliation; the engine never proposes a station; a referee run is steady-state). The rest
belongs in the two research files it cites, and C8 shows what happens when it is restated at one
remove. (ii) **§6a duplicates §§3–6** — H7 = §6.1, H9 = §3.8, H12 = §3.6, P1 = §4.2, P4 = §3.5,
P6 = §1 — and the copies have **already drifted**: §4.2 states constant gradient as a requirement
and P1 states it as a preference. (iii) **The split from `02` is eroding.** `08` restates about
twenty numbers that live in `02` — 1.30 m, 12 m, 3.0 and 2.5 m/s, Table 11, Table 12, 90°, OD160,
50 m, 3–10 %, 0.60 m. Every restatement is a second copy that can go stale, and **one already
has**: the 40 mm. Adopt the rule **`08` may cite a number in `02`; it may not restate one** — that
alone would have prevented C1 and most of M5.

---

## Verdict

**Not ready to design from.**

An engineer following `08` faithfully today would build a network that breaches at least one
guideline "shall" (minimum velocity), carry a doubled construction tolerance into a trunk with
22 % of its fall at stake, apply the depth cap in a unit its own evidence does not support, be
unable to apply two of the twelve hard constraints at all, cite Bentley for a drop-structure rule
Bentley's documentation does not support, and pass an audit that does not test the four things
that made the last iteration unissuable.

None of that is fatal to the document. The judgement in it — the objective ordering, the order of
design, the cap-and-veto ladder, the two-pass method, the retraction, the insistence that a solver
can referee hydraulics and never routing — is the most valuable thing this project has written,
and none of it is challenged by this review. What fails is the layer beneath the judgement: the
numbers, the citations and the checks.

**The shortest list that makes it fit to be binding:**

1. **H10: 40 mm → 20 mm.** One line. (C1)
2. **Add H5b, velocity ≥ 0.75 m/s at peak flow**, and state that Table 11 does not discharge it.
   Two lines plus a §10 row. (C2)
3. **Declare the depth measure once** — cover or invert — record it as the answer to W11a decision
   3 and as superseding PROJECT-STATE §2.3, and label every figure in §5.1–§5.1b with the measure
   it was computed on. (C3)
4. **Publish the tier mapping table**, and say which gradient basis binds the street-run tier.
   (C6)
5. **Rebuild §10** as one row per hard constraint plus the start-year check and a mid-reach cover
   check, and change 3.2 from a median to a maximum against Table 12. (C7)
6. **Either write up the Bentley KB sweep, or strip §9 to what the two research files support** —
   and restore "greedy", drop §9.3d, and stop citing §9.3a as vendor support for §4.4. (C8)
7. **Re-measure or delete**: the §5.1b depth histogram and the dozen untraceable numbers in §1,
   §3.2, §3.3, §3.4, §3.6 and §4.4. Use `CORRIDOR_QUALITY.md`'s 136.1 km for the wadi figure.
   (C4, C5)
8. **Reconcile the three station-reason conflicts** — H4 vs §5.1c, §5's opening vs §5.1b layer 1,
   and §5.3's commissioning station vs the three-layer attribution. Three sentences. (M1, M2, M3)

Items 1, 2, 4, 5, 6 and 8 are edits and could be done in one sitting. Items 3 and 7 need a re-run
of the breach measurement and a trace of the W10 layout metrics — perhaps half a day — and
together they are what turns the document from an argument into a specification.

Schedule M4–M14 next. **M6 (rising mains) and M12 (the 270 km of sub main and the rules that
generate it) are the two that most change what actually gets designed** — M12 in particular,
because it is the size of the job and the document does not state it.
