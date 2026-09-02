# How Bentley SewerGEMS / SewerCAD actually designs a gravity sewer

Research note, 2026-09-02. Written for the W11a design-philosophy document. Every claim below
is tagged **[Certain]** (read in Bentley's own product documentation), **[Likely]** (credible
secondary source, or forced by geometry from a documented step), or **[Guessing]** (my
inference, flagged as such). Where the documentation is silent, this note says so rather than
filling the gap.

---

## The bottom line, before the detail

**Bentley publishes a ranked priority list and a step-by-step per-pipe sequence, and both say
the same thing: the engine levels the pipe first, sizes it in the middle, then re-levels it —
and it does the whole network twice, forward then backward.** The project engineer's
recollection of "design iterations" and "a review in the reverse direction" is **confirmed by
the vendor's own help text**, with one important qualification about which product that text is
scoped to (§3).

Three things matter more than the algorithm itself:

1. **The priority list is real and it is ordered.** Eight named priorities, and the list is
   internally cross-validated — each entry names the earlier entries as the ones that override
   it. This is the most transferable artefact in the whole system and we have no equivalent.
2. **Not every constraint is enforced, and Bentley says which ones are not.** Maximum cover and
   maximum velocity "may be too limiting"; maximum slope is the *last* of eight priorities;
   maximum velocity appears in neither the priority list nor the step sequence; tractive stress
   ranks below both demoted constraints. Even minimum cover — priority 6 of 8 — is explicitly
   allowed to yield. **A clean design run is therefore not evidence that the constraints were
   met**, which is the same lesson W10 taught us the expensive way.
3. **There is no pumping station anywhere in the design loop, and no layout decision anywhere
   in it.** The engine sizes and levels a layout you draw. It will deepen a flat run until it
   runs out of catalogue or hits a cover limit it does not respect anyway. The decision to stop
   digging and pump is entirely the modeller's, in every version.

---

## Sources

| # | Source | URL |
|---|---|---|
| S1 | SewerCAD CONNECT Help — **Design Priorities** (the ranked list + the step sequence) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-53684ACF09664DEEB80ADC7BAD949D9D.html |
| S2 | SewerGEMS CONNECT Help — **Design Priorities** (textually identical to S1) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-53684ACF09664DEEB80ADC7BAD949D9D.html |
| S3 | SewerCAD Help — **Automatic Design** (parent topic) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-69F1E2898573473C8F90D56CA2DBE565.html |
| S4 | SewerCAD Help — **Using Automatic Constraint Based Design** (the 9-step workflow) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-73F4F92E-4F53-4962-98DA-096CED12833B.html |
| S5 | SewerGEMS Help — **Using Constraint Based Design** | https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20Help%20SS5-v2/en/GUID-73F4F92E-4F53-4962-98DA-096CED12833B.html |
| S6 | SewerCAD Help — **Default Design Constraints** (every constraint field) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/45010.html |
| S7 | SewerCAD Help — **Design Alternative** (what may be designed, per element) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-2B0B5EEB638F428F9114359FAF20036F.html |
| S8 | SewerCAD Help — **Design Considerations** | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-4F285ACF368340D9AE24310809626BEE.html |
| S9 | SewerCAD Help — **Conduit and Inlet Catalog Templates** | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-5BF8A370D5BF411E953A67887A27A1C7.html |
| S10 | SewerGEMS Help — **Calculation Option Attributes** (the Calculation Type field) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-EFAF5441F7114E81A6E67F13CCC217C9.html |
| S11 | SewerGEMS Help — **Solvers (Numerical)** (which solver can design) | https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-68CBF1DF0E50456B9EC0D4BFADD4E62A.html |
| S12 | SewerGEMS Help — **Switching Between Solvers** | https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-65E8C76B73E44E96B338CDA825A999D9.html |
| S13 | SewerCAD Help — **Tractive Force Design** | https://docs.bentley.com/LiveContent/web/Bentley%20SewerCAD%20SS5-v1/en/GUID-CA897907-5834-44F1-BBD4-E5B579219FF1.html |
| S14 | StormCAD Help — **Calculation Option Attributes** (used only to demonstrate the shared-help artefact in §7) | https://docs.bentley.com/LiveContent/web/Bentley%20StormCAD%20SS5-v1/en/GUID-EFAF5441F7114E81A6E67F13CCC217C9.html |

All fourteen URLs were re-checked on 2026-09-02 and return HTTP 200 with substantive content.

**Version.** SewerCAD is cited from the CONNECT Edition help; **the SewerGEMS pages self-identify
as "SewerGEMS 2024"**, so the design topic quoted throughout is current as of the 2024 release.
**[Certain]** Paths under the newer OpenFlows branding return a JavaScript application shell rather
than page content and could not be read, so a still-later revision cannot be ruled out — though
the topic being word-for-word identical across two product lines and several releases makes a
quiet rewrite unlikely.

A note on the sources: S1 and S2 are **the same page shipped in both products.** I extracted and
diffed both at word level: **1,312 words vs 1,314, and the only differences are the product banner
and "automated/automatic design" → "constraint based design".** The eight priorities, the 22-step
sequence and the reverse pass are byte-identical. Bentley maintains one design-engine help topic
across SewerCAD, SewerGEMS and StormCAD. S3 is scoped to SewerCAD but its first sentence literally begins
"StormCAD allows you to design…", which is a copy-paste artefact in Bentley's own help and
confirms the three products share one engine description. **[Certain]**

---

## 1. The design constraint set

### 1.1 What can be constrained

Everything below is from **Default Design Constraints** (S6) and **Design Alternative** (S7),
which are the same dialog reached two ways. The dialog has exactly **three tabs: Gravity Pipe,
Node, Inlet**. There is no pressure-pipe tab, no pump tab and no wet-well tab. **[Certain]**

**Gravity Pipe — Default Constraints section** (four sub-tabs):

| Constraint | Form | Verbatim definition (S6) |
|---|---|---|
| Velocity (Minimum) | Simple scalar, or **Table** vs pipe Rise | "Specify the minimum allowable velocity value." |
| Velocity (Maximum) | Simple scalar, or Table vs Rise | "Specify the maximum allowable velocity value." |
| Cover (Minimum) | Simple scalar, or Table vs Rise | "Specify the minimum allowable cover value." |
| Cover (Maximum) | Simple scalar, or Table vs Rise | "Specify the maximum allowable cover value." |
| Slope (Minimum) | Simple scalar, or Table vs Rise | "Specify the minimum allowable slope value." |
| Slope (Maximum) | Simple scalar, or Table vs Rise | "Specify the maximum allowable slope value." |
| Tractive Stress (Design Minimum) | scalar, opt-in checkbox | "the minimum tractive stress in the conduit for the flow that the designer tries to achieve during the design process" |

Two cover controls deserve their own note, because they change what "cover" means:

> "**Consider Cover Along Pipe Length?**: When this box is checked, cover along the pipe length
> is considered, by checking against the active terrain model. This ensures that any undulations
> in the surface between the ends of the pipe are taken into account when the elevations of the
> pipe are calculated. If this box is unchecked, then the cover is only considered at the start
> and end of the pipe, using the ground elevations of the start and end nodes." (S6) **[Certain]**

> "**Measure Cover To**: Choose whether cover is measured to the pipe soffit or crown." (S6)
> **[Certain]**

**Gravity Pipe — Extended Design section** (three sub-tabs):

| Option | Verbatim (S6) |
|---|---|
| Is Part Full Design? / Percentage Full | "allows you to specify the Percent Full target to be used by the design algorithm"; Simple scalar or Table vs Rise. S4 adds: "The design percentage is defined as a percentage of full depth." |
| Allow Multiple Barrels? / Maximum Number of Barrels | "allows the design algorithm to use more than one identical section in parallel, up to the specified Maximum Number of Barrels" |
| Limit Section Size? / Maximum Rise | "limits the pipe section height to the specified Maximum Rise value during the design process… If none of the available design sections have a small enough rise, the smallest one will be used." |

**Node tab** (gravity structures):

> "During an automatic design, the program will adjust the elevations of the pipes adjacent to
> the structure according to the structure's matching constraints. The two choices for matching
> are **Inverts** and **Crowns**. Additionally, the downstream pipe can be offset from the
> upstream pipe(s) by a specified amount. This value is called the **Matchline Offset**.
> Optionally, the program supports the design of **drop structures**. In some situations, drop
> structures can minimize pipe cover depths while maintaining adequate hydraulic performance."
> (S6) **[Certain]**

S7 adds the geometric definitions:

> "The depth of drop structure is measured vertically from the downstream invert of the incoming
> pipe to the sump elevation of the structure. The depth of cover is measured as the vertical
> distance between ground elevation and the pipe crown at each end." **[Certain]**

Note the tension in Bentley's own wording: the Node tab says cover is measured to the **crown**,
while the Gravity Pipe tab lets you choose **soffit or crown**. For a circular pipe these are the
same thing; for a box culvert they are not. Not resolved in the documentation. **[Certain]** that
both statements exist; **cannot tell** which governs for non-circular sections.

**Soffit / invert / crown matching** is therefore *not* a pipe constraint at all in this software
— it is a **node** constraint, expressed as `match on {Inverts | Crowns} + Matchline Offset`.
That is a cleaner formulation than treating it as a per-pipe rule and is worth borrowing.

**Per-element override.** Any element can escape the global values:

> "You can modify the constraints for just an individual element by checking **Specify Local Pipe
> (Inlet) Constraints** box associated with that element." (S4) **[Certain]**

**What may be designed, per element** (S4, S7) — this is the complete list of decision variables:

- Conduits: `Design Conduit?` (i.e. size), `Design Start Invert?`, `Design Stop Invert?`
- Nodes: `Design Structure Elevation?` (sump elevation), `Desired Sump Depth`
  ("the distance below the lowest pipe invert"), `Allow Drop Structure?`
- Catch basin inlets: `Design Inlet Opening?`

> "Unchecking them means that the values set in the initial model will be maintained." (S4)
> **[Certain]**

**Candidate diameters are not continuous.** They come from a catalogue the modeller populates:

> "When performing an Automatic Design, the software suggests only conduit and inlet types that
> are contained within the Conduit and Inlet Catalogs. A new model starts with empty Conduit and
> Inlet Catalogs." (S9) **[Certain]**

> "Automated conduit sizing only relates to closed conduits such as circular and elliptical pipes
> and box conduits, **not open channels**." (S4) **[Certain]**

### 1.2 Hard, preference, or reported — the honest classification

Bentley does not publish a hard/soft table. But the Design Priorities page (S1) is explicit that
**nothing here is hard except the catalogue itself**, and it names which constraints it expects
to abandon. Reading the priority list and the "Other Constraints" paragraph together:

| Constraint | Class | Evidence |
|---|---|---|
| Available catalogue sizes | **Hard** — the only true hard constraint | Every fallback in S1 resolves to "the smallest available", "the largest available size and number of barrels" |
| Fit within adjacent **existing** structure | **Near-hard** (priority 1) | Violated only "if there are no available section sizes that would not violate that condition" |
| Capacity ≥ discharge | **Strong preference** (priority 3) | "If site restrictions or available section limitations result in a situation where no sections meet the required capacity, the largest available size and number of barrels will be chosen" — i.e. it gives up and reports an undersized pipe |
| Downstream ≥ upstream diameter | **Preference** (priority 4) | "Designs typically avoid…" |
| Invert/crown matching (downstream) | **Preference** (priority 5) | "because of higher design priorities… the matching criteria may not always be met" |
| **Minimum cover** | **Preference** (priority 6) | "higher design priorities, such as existing structure locations and matching criteria, may prevent the minimum cover constraint from being met" |
| Invert/crown matching (upstream) | **Preference** (priority 7) | "Higher design priorities, such as minimum cover constraints, may result in a pipe that does not match upstream as desired" |
| **Maximum slope** | **Weak preference** (priority 8, last) | "may be violated if higher priority design considerations… governs" |
| **Minimum velocity** | **Acted on, unranked** | Not in the priority list. Appears as an explicit step (§2.2 step 15). S1: "Several constraints that are not mentioned above, such as minimum velocity constraints and minimum slope constraints, may also result in adjustments" |
| **Minimum slope** | **Acted on, unranked** | Same. Appears three times in the step sequence |
| **Maximum cover** | **Demoted — effectively advisory** | S1: "Other constraints may be too limiting, such as maximum cover constraint and maximum velocity, resulting in designed pipes that could violate too many other constraints" |
| **Maximum velocity** | **Demoted — effectively advisory** | Same sentence. It appears **nowhere** in the published step sequence |
| Tractive stress (minimum) | **Weakest** | S6: "note: the maximum cover and maximum velocity are of more priority than tractive stress if there are conflicts" — i.e. below two constraints that are themselves described as too limiting |

**[Certain]** on every quote. **[Likely]** on the class labels, which are my reading of Bentley's
own hedging language, not their published taxonomy.

The tractive-stress note is the only place in the whole documentation set where Bentley states a
priority *between* two named constraints outside the main list, and it puts tractive stress at
the bottom. If PAM-GUD-203 self-cleansing is to be enforced by tractive force rather than by
minimum velocity, **the software will be the last thing to enforce it.**

---

## 2. The order in which constraints are applied

This is the core of the question, and Bentley answers it twice: once as a ranked list of
priorities, once as an explicit numbered step sequence.

### 2.1 The published priority list — verbatim, in order

From S1/S2. The framing sentences first:

> "Unfortunately, it is not always possible to automate a design that meets all desired
> constraints. With this in mind, there are certain priorities that are considered when the
> automated design is performed. These priorities are in place to try to minimize the effect on
> existing portions of the system while providing appropriate capacity in the designed pipes.
>
> While this sequence does not go into complete detail regarding the design process, it does
> indicate the general priorities for the automated design. The priorities, of course, only deal
> with elements that are being designed. If a pipe has fixed inverts or is not to be designed at
> all, some or all of these criteria obviously do not apply."

The eight priorities, **in the order Bentley presents them**:

1. **A Designed Pipe Should Fit within Adjacent Existing Structures**
   > "If a pipe connects to an existing structure, the pipe rise should be completely within the
   > existing structure. The only time this may be violated is if there are no available section
   > sizes that would not violate that condition… In this very unlikely condition, the smallest
   > available section size will be selected, with the invert elevation placed at the bottom of
   > the structure."

2. **A Designed Pipe Should Not Have a Crown Above an Adjacent Designed Structure**
   > "Where pipe inverts are fixed, it is possible that the required section size would cause the
   > pipe crown to be higher than the top elevation of an adjacent designed structure. If all
   > available pipe section rises are greater than the depth of the pipe invert, the smallest pipe
   > size will be chosen."

3. **Pipe Capacity Should Be Greater Than the Discharge**
   > "If the pipe is not limited by adjacent structures, the pipe should be sized such that the
   > design capacity is greater than the calculated discharge in the pipe. The design capacity may
   > be based on one or more pipes, flowing full or part-full, depending on user-set design
   > options. If site restrictions or available section limitations result in a situation where no
   > sections meet the required capacity, the largest available size and number of barrels will be
   > chosen."

4. **Downstream Pipes Should Be at Least as Large as Upstream Pipes**
   > "Designs typically avoid sizing downstream pipes smaller than upstream pipes, regardless of
   > differing slope and velocity requirements. One of the primary reasons for this is debris that
   > passes through the upstream pipe could become caught in the connecting structure, clogging
   > the sewer."

5. **Pipe Matching Criteria Downstream Should Be Met**
   > "Whenever possible, the designed pipe should have its downstream invert set such that the
   > pipe meets the matching criteria, such as matching inverts or crowns. Note that because of
   > higher design priorities, such as the pipe fitting within existing structures, the matching
   > criteria may not always be met."

6. **Minimum Cover Constraint Should Be Met**
   > "Pipe inverts should be set such that the upstream and downstream crowns of the pipe are
   > below the ground elevation by at least the amount of the minimum cover. Note that higher
   > design priorities, such as existing structure locations and matching criteria, may prevent
   > the minimum cover constraint from being met."

7. **Pipe Matching Criteria Upstream Should Be Met**
   > "The upstream invert of the designed pipe should be set to meet the matching criteria of the
   > upstream structure. Higher design priorities, such as minimum cover constraints, may result
   > in a pipe that does not match upstream as desired."

8. **Maximum Slope Constraint Should Be Met**
   > "Wherever possible, the designed pipe should not exceed the desired maximum slope. In some
   > situations, elevation differences across the system may result in a case where a drop
   > structure can be used to offset pipes. This is used instead of a pipe that is too steep, or
   > instead of upstream piping that would require much more excavation. Note that the maximum
   > slope constraint may be violated if higher priority design considerations, such as existing
   > structure location or pipe matching criteria, governs."

Then the closing:

> "**Other Constraints and Considerations.** There are many degrees of freedom when designing a
> piping system. Several constraints that are not mentioned above, such as minimum velocity
> constraints and minimum slope constraints, may also result in adjustments to the designed pipe.
> Other constraints may be too limiting, such as maximum cover constraint and maximum velocity,
> resulting in designed pipes that could violate too many other constraints.
>
> This wide range of choices and priorities emphasizes the need for careful review of any
> automated design by a professional. It is not always possible to meet every desired condition,
> so it is very much the responsibility of the engineer to make final judgments and decisions
> regarding the best design for the client."

**This list is genuinely ordered, not just a discussion sequence.** I cross-checked it against
itself: every entry that names an overriding constraint names one that appears *earlier* in the
list. #5 is overridden by #1; #6 by #1/#2 and #5; #7 by #6; #8 by #1 and #5/#7. Four independent
back-references, zero contradictions. **[Certain]** that the list is self-consistent as a
priority ranking.

### 2.2 The step sequence — does it size then level, or level then size?

**Neither. It brackets the size, levels, sizes, then re-levels.** S1/S2 publish the actual per-
pipe sequence. **Read the scoping caveat in §3.1 before quoting this as SewerGEMS behaviour.**

Verbatim (S1), for the forward pass:

> "the design steps for **one pipe** in design from upstream to downstream will be the following:
>
> 1. Calculate flow travel time of non-design pipe if including flow travel time is selected
> 2. Conduit discharge calculation (Include flow travel time in system Tc calculation)
> 3. Get conduit minimum size
> 4. Get conduit maximum size
> 5. Adjust upstream invert to match upstream minimum cover
> 6. Adjust upstream invert to match upstream structure (to match matchline offset)
> 7. Adjust downstream invert to match downstream minimum cover
> 8. Adjust downstream invert to match minimum slope
> 9. Adjust downstream invert to match downstream fixed structure
> 10. Adjust upstream invert to match maximum slope
> 11. Adjust upstream invert to match fixed structure
> 12. Adjust downstream invert to match minimum slope
> 13. Adjust downstream invert to match fixed structure
> 14. **Adjust conduit size for Capacity to match discharge** (Calculate conduit flow travel time if including flow travel time is selected)
> 15. Adjust downstream invert to match minimum velocity
> 16. Adjust both ends to match Upstream structure (to match matchline offset)
> 17. Adjust both ends to match upstream minimum cover
> 18. Adjust downstream invert to match downstream minimum cover
> 19. Adjust upstream invert to match maximum slope
> 20. Adjust upstream invert to match fixed structure
> 21. Adjust downstream invert to match minimum slope
> 22. Adjust downstream invert to match fixed structure"

**The structure of that sequence, read as an engineer:**

| Phase | Steps | What it does |
|---|---|---|
| Load | 1–2 | Compute the discharge in this reach |
| **Bracket** | 3–4 | Establish the feasible diameter *range* (min and max), not the diameter |
| **Level A** | 5–13 | Nine invert moves: cover → matchline → min slope → fixed structures → max slope → min slope again |
| **Size** | 14 | Pick the diameter that gives capacity ≥ discharge |
| Velocity | 15 | One invert move for minimum velocity |
| **Level B** | 16–22 | Seven invert moves, largely repeating Level A with a different opening order |

So: **the levels are set before the diameter is chosen, then reset after it.** This makes physical
sense — you cannot know the required capacity-controlling gradient until you have a gradient, and
you cannot finalise the invert until you know the rise. Bentley resolves the circularity by
levelling on a bracketed size, sizing once, and re-levelling. It does **not** iterate size↔level
to convergence. **[Certain]** on the sequence; **[Likely]** on the reading.

**Level A and Level B are not identical, and the difference is informative:**

- Level A opens `min cover → matchline`; Level B opens `matchline → min cover`.
- Level A adjusts one end at a time; Level B steps 16–17 adjust **"both ends"** — i.e. it
  translates the whole pipe rigidly rather than rotating it. That preserves the gradient chosen in
  step 14 while re-seating the pipe against the upstream structure and cover. **[Likely]**
- Both blocks end with the identical four-step tail:
  `max slope → fixed structure → min slope → fixed structure`.

**That tail answers the conflict questions directly.** Within a pass, the *last* rule applied is
the one that wins on a residual conflict, and the last rule is **minimum slope**, clamped to fixed
structures. So on flat ground where minimum slope and something else disagree, **minimum slope
wins and the pipe goes deeper.** **[Likely]** — this is inference from ordering, not a Bentley
statement, but it is a strong inference: an adjustment applied after another adjustment overwrites
it.

**Two conflicts the documentation does not resolve, and I will not pretend it does:**

- *Minimum cover vs minimum slope on flat ground.* Both are acted on. Min slope is applied after
  min cover in both blocks, and min slope is satisfied by **lowering the downstream invert**,
  which only *increases* cover — so on a flat run these two do not actually fight. They both push
  the pipe down. **Nothing in the sequence stops that descent.** See §5. **[Likely]**
- *Minimum velocity vs maximum velocity on steep ground.* Step 15 acts on minimum velocity.
  **Maximum velocity appears nowhere in the 22 steps.** Combined with S1's statement that maximum
  velocity "may be too limiting", the honest reading is that maximum velocity is checked and
  reported but **not designed to**. **[Likely]**

There is also a **tension between the priority list and the step list** that I cannot resolve from
the documentation. The list puts minimum cover (#6) above maximum slope (#8); the step sequence
applies maximum slope (steps 19–20) *after* minimum cover (steps 17–18). If those two disagreed,
the sequence would let max slope override min cover, contrary to the stated ranking. In practice
they probably do not disagree — satisfying max slope means lowering the upstream invert, which
*increases* upstream cover — so the ordering may simply be safe rather than contradictory.
**[Guessing]** on the reconciliation. Flagged because a design philosophy document should not
assert a resolution the vendor never published.

---

## 3. Does it iterate, and in which directions?

### 3.1 Two passes, forward then reverse — confirmed, with a caveat

Verbatim (S1/S2), immediately after the 22 steps:

> "After designing all pipes from upstream to downstream, we design all pipes from downstream to
> upstream. For each conduit, we run the following main steps:
>
> 1. Adjust downstream structure elevation to match conduit downstream invert
> 2. Adjust conduit downstream invert to match fixed structure
> 3. Adjust conduit upstream invert to match maximum slope
> 4. Adjust conduit upstream invert to match fixed structure"

**This confirms the project engineer's recollection of a review in the reverse direction.**
**[Certain]** that Bentley documents it.

**The caveat, stated plainly.** This entire section — the 22 steps *and* the reverse pass — sits
under the heading **"Design Steps When Conduit Flow Travel Time Is Considered (StormCAD Only)"**.
So:

- **[Certain]** the text appears verbatim in the SewerCAD help *and* the SewerGEMS help, not only
  StormCAD's. I fetched both and diffed them.
- **[Certain]** the heading scopes the *travel-time option* to StormCAD (travel time in Tc is a
  rational-method / storm concept; it is irrelevant to sanitary peak flows).
- **[Likely]** the underlying two-pass, per-pipe machinery is the same engine in all three
  products, with steps 1–2 (travel time and Tc) simply inapplicable to sanitary design. Supporting
  evidence: the products share one engine and one help topic (§Sources note), and the priority
  list above it carries no product qualifier.
- **Cannot tell** whether the sanitary (GVF-Convex) path executes exactly these 22 steps in exactly
  this order. Bentley has not published a sanitary-specific step list.

**Do not write "SewerGEMS performs 22 steps" into a client document.** Write "Bentley's published
description of the design engine is a 22-step forward pass followed by a 4-step reverse pass",
and footnote the scoping.

### 3.2 What the reverse pass is actually for

Read it against the forward pass. The reverse pass has **no sizing step, no cover step, no minimum
slope step and no capacity step**. It does exactly two things: it **seats the structures onto the
inverts the forward pass produced** (step 1: move the manhole to match the pipe, not the pipe to
match the manhole), and it **re-checks maximum slope** on the way back up.

That is a *reconciliation* pass, not a re-optimisation. It fixes the one thing a forward-only
sweep cannot: a downstream decision that invalidates an upstream structure elevation. **[Likely]**

### 3.3 Convergence — there is none for design

**The documentation defines no convergence criterion for the design loop, no relaxation, no retry,
and no pass count beyond the two described.** Two passes, fixed, then done. **[Certain]** that no
such criterion is published; **[Likely]** that none exists, since Bentley documents convergence
controls in detail everywhere else.

For contrast, here is what Bentley *does* publish convergence controls for, all of which are
**hydraulic** solution controls under Gravity Hydraulics or the dynamic solvers, **not** design
controls (S10):

> "**Maximum Network Transversals** — Maximum number of iterations that will be performed when
> solving GVF equations."
>
> "**Flow Convergence Test** — This value is taken as the maximum relative change in discharge
> occurring at the system outfall between two successive network solutions… it is necessary to
> iterate until the system balances, or a maximum number of trials has occurred."

Do not confuse these with design iteration. They converge the *hydraulics* of a given geometry.
**[Certain]**

### 3.4 Is it global or reach-by-reach?

**Reach-by-reach, sequential, and greedy.** Bentley's own phrasing gives it away: "the design steps
for **one pipe**…" and "**For each conduit**, we run the following main steps". The engine walks the
network pipe by pipe. **[Certain]** on the wording; **[Likely]** on the "greedy" label — Bentley
never uses it.

Bentley states an *aim* that sounds like optimisation:

> "In general, the design algorithm attempts to minimize excavation, which is typically the most
> expensive part of installing sewer piping and structures." (S3) **[Certain]**

But **no objective function, no cost model, no search method and no optimality claim is published
anywhere.** "Minimize excavation" is realised through the priority ordering and through drop
structures, not through a solver. Marketing copy that says the software "recommends the most
cost-effective pipe sizes and invert elevations" is describing the same greedy heuristic.
**[Likely]** — I could find no Bentley document describing an optimisation algorithm, and absence
across the full help set is meaningful.

---

## 4. Steep ground

**What is documented:**

> "Wherever possible, the designed pipe should not exceed the desired maximum slope. In some
> situations, elevation differences across the system may result in a case where **a drop structure
> can be used to offset pipes. This is used instead of a pipe that is too steep, or instead of
> upstream piping that would require much more excavation.**" (S1) **[Certain]**

> "Optionally, the program supports the design of drop structures. In some situations, drop
> structures can minimize pipe cover depths while maintaining adequate hydraulic performance."
> (S6) **[Certain]**

> `Allow Drop Structure?` is a **per-node checkbox** in the Design Alternative. (S4, S7)
> **[Certain]**

**So the answer to "does it hold the pipe parallel to the ground and cap velocity, or step it
down?" is: it steps it down — but only if you let it, and only against maximum *slope*, never
against maximum *velocity*.**

Mechanism, reading the steps: on a reach steeper than the maximum, steps 10/19 "Adjust upstream
invert to match maximum slope". Reducing slope means either lowering the upstream invert or raising
the downstream one; the downstream end has already been clamped to a fixed structure, so the move
is **downward at the upstream end**. That buys the gradient at the price of excavation, and it
propagates upstream through the next reach's matching constraint. **[Likely]** — the direction is
forced by geometry, not stated.

**The drop structure is the release valve for exactly that cost.** Bentley says so in the sentence
above: the drop is used "instead of upstream piping that would require much more excavation".
**[Certain]**

**What is NOT documented, and I will not guess:**

- The **trigger condition** for inserting a drop. Nothing says "when slope exceeds X" or "when the
  required excavation exceeds Y". **Cannot tell.**
- **How the drop height is chosen.** S7 defines how a drop is *measured* ("vertically from the
  downstream invert of the incoming pipe to the sump elevation of the structure") but not how it
  is *sized*. **Cannot tell.**
- **Whether there is a maximum drop.** No maximum-drop constraint exists in the Node tab.
  **Cannot tell.**
- **What happens when ground slope exceeds the maximum-velocity slope.** Maximum velocity is not in
  the priority list and not in the 22 steps. The only statement is S1's "Other constraints may be
  too limiting, such as maximum cover constraint and maximum velocity, resulting in designed pipes
  that could violate too many other constraints." The honest reading: **the engine does not design
  to maximum velocity at all.** **[Likely]** — inference from two independent omissions plus one
  explicit demotion, but Bentley never says "maximum velocity is ignored during design".

---

## 5. Flat ground and deep excavation

**At what point does it stop deepening? The documentation gives no satisfying answer, and that is
itself the finding.**

What we know:

1. **Minimum slope is enforced by lowering the downstream invert** (steps 8, 12, 21). On a flat run
   every reach inherits a deeper invert from the one above. **[Likely]**
2. **Minimum slope is applied last in both levelling blocks**, so within a reach it wins the
   residual conflict. **[Likely]**
3. **Maximum cover exists as a constraint** (S6, Cover tab) — but Bentley itself puts it in the
   "may be too limiting" category and it appears **nowhere** in the 22-step sequence. **[Certain]**
   that it is absent from the sequence.
4. **`Limit Section Size?` / Maximum Rise is a real stop**, but it stops the *diameter*, not the
   depth: "If none of the available design sections have a small enough rise, the smallest one will
   be used." (S6) **[Certain]**
5. The only genuine hard floor is the **catalogue** and any **fixed structure** the modeller has
   set (`Design Start/Stop Invert? = False`). **[Likely]**

**Conclusion: the engine will keep going deeper. The stopping rule is the modeller's, imposed by
fixing inverts or by not designing certain reaches.** **[Likely]** — no Bentley statement to the
contrary was found, and maximum cover being both present as a field and absent from the sequence is
consistent with it being reported rather than designed to.

**Is a pumping station ever in the design loop?**

**No. Categorically no, and the evidence is structural rather than a single quote:**

- The Design Alternative and Default Design Constraints dialogs contain exactly three element
  classes: **Gravity Pipe, Node, Inlet** (S6, S7). There is no pump, wet well, pressure pipe or
  force main tab. **[Certain]**
- The complete list of design decision variables (S4) is: conduit size, start invert, stop invert,
  structure sump elevation, drop structure allowance, inlet opening length. **[Certain]**
- The parent topic scopes the whole feature to "gravity piping and structures" (S3). **[Certain]**
- The Calculation Type field defines a design run as "**pipe and invert sizing**" (S10, quoted in
  full in §7). **[Certain]**

So: **the decision to stop digging and lift is always the modeller's**, in every version of the
product. Nothing in the engine will propose a station, site one, or tell you that you should have.
It will simply return a very deep pipe. **[Likely]** that this is a complete statement — it rests on
absence across four documents, but the absence is total and consistent.

For our project this is not a limitation to work around; it is a **confirmation that the pumping
decision belongs upstream of any hydraulic engine**, which is exactly where W8 and W11a put it.

---

## 6. What it does NOT do

Stated as plainly as the evidence allows, because this section carries as much weight as the rest.

| It does not… | Confidence | Basis |
|---|---|---|
| **Choose layout, routing, or which street a pipe runs down** | **[Likely]**, very strong | The design decision variables (S4) are size, two inverts, sump elevation, drop allowance, inlet length. No geometry, no connectivity, no node placement. You draw the network; it sizes and levels it. Bentley never claims otherwise anywhere in the help set |
| **Add, delete, move or re-connect any element** | **[Likely]** | Same basis. Step 1 of the workflow is "Create a model with all the elements to be designed" (S4) |
| **Choose manhole spacing** | **[Likely]** | No spacing constraint exists in any of the three tabs |
| **Optimise anything globally** | **[Likely]** | Processes "one pipe" / "each conduit" at a time (S1). No objective function, cost model or search method published. "Minimize excavation" (S3) is an aim realised by the priority ordering |
| **Design pumps, wet wells, force mains or pressure pipes** | **[Certain]** on the dialogs; **[Likely]** as a complete statement | §5 |
| **Design open channels** | **[Certain]** | "Automated conduit sizing only relates to closed conduits… not open channels" (S4) |
| **Select a different inlet type** | **[Certain]** | "will not select a different Catalog Inlet during the design run, it will only select a different opening length for the inlet specified" (S4) |
| **Invent a diameter** | **[Certain]** | "suggests only conduit and inlet types that are contained within the Conduit and Inlet Catalogs" (S9) |
| **Design to maximum velocity** | **[Likely]** | Absent from the priority list and from all 22 steps; explicitly demoted as "too limiting" (S1) |
| **Guarantee any constraint is met** | **[Certain]** | "It is not always possible to meet every desired condition" (S1) |
| **Run under the Implicit or Explicit (SWMM) solver** | **[Certain]** | No design property exists in either solver's calculation-option group (S10). §7 |
| **Run as an extended-period simulation** | **[Certain]** | Design is a GVF-Convex **steady-state** option only (S10) |
| **Iterate to convergence** | **[Certain]** no criterion is published | §3.3 |

And Bentley's own closing position, which is worth quoting to a client verbatim:

> "As with any automated design, the program's design is intended only as a preliminary step. It
> will select pipe sizes and pipe invert elevations based on the input provided, but no computer
> program can match the skills that an experienced engineer has. The modeler should always review
> any automated design, and should make any changes required to adjust, improve, and otherwise
> polish the system." (S8, *Design Considerations*) **[Certain]**

---

## 7. Design vs Analysis mode, and what design writes back

**Design is a scenario-level calculation option, not a command.** (S4) **[Certain]**

> "set the scenario's **Calculation Type** (found in the calculation options) to **Design** as
> opposed to Analysis." (S4)

The field definition, which contains three separate constraints in one sentence (S10):

> "**Calculation Type** — For a **GVF-convex steady state** simulation, this property establishes
> whether an analysis (simulation) or a **design (pipe and invert sizing)** run is to be made.
> **Default = Analysis.**" **[Certain]**

Unpacked:

1. **Solver constraint — design belongs to the GVF solvers, not the dynamic ones.** SewerGEMS
   carries all four solvers; SewerCAD carries GVF-Convex only; StormCAD carries GVF-Rational only
   (S11, "Available Solvers by Product" table). **[Certain]**
   The Calculation Type field quoted above scopes design to "GVF-convex steady state". **But treat
   that wording carefully:** I fetched the same Calculation Option Attributes page from the
   **StormCAD** help and it carries the *identical* sentence — "For a GVF-convex steady state
   simulation…" — even though StormCAD cannot run GVF-Convex at all. It is another shared-help
   artefact, so the sentence does not cleanly prove that GVF-Rational cannot design; StormCAD
   plainly does design, on GVF-Rational. **[Certain]** that both pages carry the same sentence.
   What the documentation *does* establish: **no design property exists in the Implicit or
   Explicit calculation-option groups at all**, so the two dynamic-wave solvers analyse only.
   **[Certain]** For our sanitary work the question is academic — GVF-Convex is the relevant
   solver, and there design is available and steady-state only.
2. **Time constraint.** Design requires **steady state**. S10: "If Steady State is selected, most of
   the time related properties below are not available and **the only additional property in this
   category is Calculation Type.**" So a design run is against a **steady peak flow**, never a
   dynamic hydrograph. **[Certain]**
3. **Scope.** A design run is defined as **"pipe and invert sizing"**. That is the whole of it.
   **[Certain]**

**What design writes back, and where:**

> "Changes suggested to the model by an automatic design calculation will be saved to the
> **Physical Alternative** that you specify. This Physical Alternative should be uniquely created
> just for the automatic design **to avoid overwriting the data in your other Physical
> Alternatives**." (S3) **[Certain]**

> "When the design starts, it will indicate the (current) Physical Alternative in which the results
> will be stored. If the user wants the results stored there, pick Yes. If the user wants the new
> design properties stored in another Physical Alternative, this is the place to specify that
> alternative by picking No." (S4) **[Certain]**

This is the single best piece of software engineering in the whole feature and it maps directly
onto our W# rule: **the design writes into a named, separate container, and the input is never
silently overwritten.** Bentley's Physical Alternative is our `W#` folder.

The values written back are the decision variables of §1.1: conduit size (and barrel count),
start invert, stop invert, structure sump elevation, drop structure, inlet opening length.
**[Likely]** — assembled from the decision-variable list plus "pipe and invert sizing", not stated
as a single list anywhere.

**Whether design writes explicit constraint-violation flags: cannot tell.** SewerGEMS has a User
Notifications Manager for validation warnings and errors, but I found no documentation of
design-specific violation messages, and none of the design help topics mentions reporting. Given
that Bentley expects constraints to be violated routinely, some reporting mechanism almost
certainly exists — but I could not confirm what it is, so **do not assert that the software tells
you which constraint it abandoned.** **[Guessing]** that it does.

---

## 8. Bentley's recommended workflow

The nine steps from **Using Automatic Constraint Based Design** (S4), condensed but faithful.
**[Certain]** on all of it.

**Before designing:**

1. **Build the complete model and make it run in Analysis first.** "Create a model with all the
   elements to be designed. Make initial estimates of the decision variables such as conduit size
   and invert elevations. **Run the model to make sure that it is complete and will calculate
   without fatal errors.**" — Design is never the first calculation. A geometry that will not
   analyse will not design.
2. **Populate the Conduit Catalog.** "These candidate conduits should have the same conduit shape
   and material as the pipe in the original model. There must be at least one conduit in the
   Conduit Catalog with the same shape (e.g. circular) and material (e.g. PVC) as the conduit being
   designed." Recommended method: "build it using the **Import from Library** command and then
   picking the shape and material from the list in the library, **then deleting those sizes that
   should not be considered in design.**"
3. **Set the Design Alternative** — which elements get designed, and which properties of each.
   "If you do not want the Start (Upstream) and/or Stop (Downstream) invert elevations to change
   during the design, you must set the Design Start Invert? and/or Design Stop Invert? property to
   False."
4. **Set the constraints** — globally via `Analysis > Default Design Constraints`, then override
   per element. "If you set up constraints under Default Design Constraints… these constraints will
   be used for any new Design Alternative as well as the alternative associated with the current
   scenario." A useful trick Bentley states outright: "**If you do not want to use velocity
   constraints, set the Minimum to zero and Maximum to a large number.**"
5. **Set Extended Design** — part-full percentage, multiple barrels, maximum rise.
6. **Create a Calculation Option with Calculation Type = Design.**
7. **Create a new scenario** pairing that Design Alternative with that Calculation Option, make it
   current, Compute.
8. **Direct the output to a dedicated Physical Alternative** (§7).

**After designing:**

9. **Review it as an engineer.** S8 in full, quoted in §6. S1: "This wide range of choices and
   priorities emphasizes the need for careful review of any automated design by a professional."

The shape of that workflow is worth noticing independently of the software: **fix the geometry,
fix the catalogue, fix the constraints, declare what is free and what is frozen, run once, review.**
It is a pipeline with an explicit frozen/free declaration, and that declaration is per element.

---

## 9. What this means for our design philosophy

### 9.1 Adopt

**A1 — A written, ranked priority list, and print the winner on every reach.**
This is the single most valuable thing in the entire research. Bentley's list is eight entries,
ordered, self-consistent, and published so that a reviewer can predict what the software will
sacrifice. **We have no equivalent.** W10 shipped 2.80 km of surcharged trunk, 10.68 km over the
d/D limit and 45.92 km below minimum cover, and the reason nothing caught it is not only that the
auditor was missing (P1) — it is that **there was never a written statement of which rule yields
when two disagree**, so there was nothing to audit against.

Concretely, for W11a: a `PRIORITY.md` table of our own constraints in rank order, each traced to
its G203/G201/G202 page, and a `GOVERNED_BY` field written onto every reach naming the rule that
set its invert. Bentley's own back-reference pattern ("higher design priorities, such as X, may
prevent Y") is the validation test — if our list cannot pass that self-consistency check, it is not
a ranking.

**A2 — Bracket, level, size, re-level. In that order, and only once.**
The circularity of gradient and diameter is real, and Bentley's resolution is cheap and defensible:
establish the feasible diameter range, set the levels on it, pick the diameter for capacity, then
re-seat the levels rigidly (both ends together) so the chosen gradient survives. No iteration to
convergence, no oscillation. Our sizing step should be restructured to this shape. Note especially
step 16–17's **"adjust both ends"** — translating the pipe rather than rotating it preserves the
gradient decision, and our 0.05 % rounded-gradient rule makes that even more important, because a
rotation would destroy the round number the drawing depends on.

**A3 — A reverse reconciliation pass that moves structures to pipes, not pipes to structures.**
The four-step reverse pass is not a re-design. Its first step is "**Adjust downstream structure
elevation to match conduit downstream invert**" — the manhole yields to the pipe, once the pipe is
settled. That is the correct direction of authority and it is a small, bounded, cheap pass. It also
directly confirms what the project engineer remembered, so it can be cited in the report.

**A4 — Constraint severity classes, declared, not assumed.**
Bentley classifies in prose: hard (catalogue), near-hard (existing structures), preference (cover,
matching), and explicitly demoted (max cover, max velocity, tractive stress). Our 59-check contract
currently splits 50 blocking / 9 reporting — a two-class system. **Three or four classes would be
more honest**, because "capacity ≥ discharge" and "matching soffits at a manhole" are not the same
kind of obligation and treating them identically is how a check registry becomes noise that gets
ignored.

**A5 — Cover measured along the pipe, against the terrain, not just at the two nodes.**
Bentley makes this a checkbox: "any undulations in the surface between the ends of the pipe are
taken into account". We have a 0.5 m bare-earth VRT and reaches that run to 6,541 m in W10. Node-
only cover checking on a 6.5 km reach is meaningless. This is a free correctness win and it is
already in our data.

**A6 — Output to a dedicated container that is never the input.**
Design results go to a separate Physical Alternative "to avoid overwriting the data in your other
Physical Alternatives". This is our `W#` rule, arrived at independently by a commercial vendor for
the same reason. Worth citing in the report as external validation of the iteration doctrine.

### 9.2 Reject

**R1 — Reject reach-by-reach greedy as the basis for option comparison.**
Bentley's engine is sequential and per-pipe with no global objective, and it says "minimize
excavation" without publishing a cost model. That is acceptable for detailing a layout somebody
already decided. **It is not acceptable for choosing between three concept options over 25 years at
5 %.** Our options doctrine (seven criteria, NPV, life-cycle cost) sits at a level the design engine
does not operate at, and we should not let a hydraulic tool's local optimisation masquerade as
scheme optimisation. Whole-scheme cost stays in our own layer.

**R2 — Reject the demotion of maximum velocity and maximum cover.**
Bentley's judgement that these are "too limiting" is a judgement about *its own algorithm's ability
to satisfy them*, not about whether they matter. For us:
- **Maximum velocity** is a G203 requirement and an abrasion/scour issue in a system with this much
  fall. It must be a real check with a real class, not inherited as advisory.
- **Maximum cover** is our **12 m rule (G203 p33)**, and it is the single constraint that determines
  whether a pumping station exists. Adopting Bentley's demotion of it would be adopting the exact
  failure mode W10 already had.

**R3 — Reject any expectation that the tool decides pumping.**
Confirmed in §5: no pump, wet well or force main appears anywhere in the design loop, in any
version. The engine deepens until the modeller stops it. Our SLS consolidation doctrine (rule 9)
must therefore run **before** any hydraulic design pass and hand it a layout with the stations
already sited — which is what W8 did and what W11a should keep.

**R4 — Reject "the software met the constraints" as a form of evidence.**
Bentley states in writing that constraints will be violated and that the engineer is responsible.
If SewerGEMS is used as the referee run (per the standing hydraulics-first doctrine), a clean
compute is not a pass. **Our auditor checks the design; SewerGEMS checks the hydraulics.** They are
not substitutes, and the report should say so.

### 9.3 Cannot tell — do not write these into a permanent document

| Question | Status |
|---|---|
| Whether the 22-step sequence applies unchanged to sanitary GVF-Convex design | Documented only under a heading reading "(StormCAD Only)", though it ships in all three products' help. **Unresolved** |
| What triggers a drop structure, how its height is chosen, whether a maximum drop exists | **Not documented anywhere.** Only the measurement definition is published |
| Whether the engine ever reports *which* constraint it abandoned on a given reach | **Not documented.** A User Notifications mechanism exists generally; no design-specific messages found |
| Whether design is ever run more than the two documented passes | **No convergence criterion published for design.** Two passes appears to be the whole of it, but Bentley never says "two passes and stop" |
| Whether maximum velocity is checked at all during design, or only after | **Absent from priority list and from all 22 steps.** Demoted in prose. The strong reading is "not designed to", but Bentley never states it |
| Whether the priority list or the step sequence governs where they disagree (min cover vs max slope, §2.2) | **Unresolved.** Probably moot in practice, but not documented |
| Any published cost model or optimisation method behind "minimize excavation" | **None found** across the full help set |

---

## 10. One-paragraph summary for the report

> Bentley's automated ("constraint-based") design in SewerGEMS and SewerCAD sizes and levels a
> network the engineer has already laid out. It does not choose routes, spacing, connectivity or
> pumping. Working one reach at a time from the head of the system down, it brackets the feasible
> diameter range, sets the inverts against cover, structure-matching and slope limits, selects the
> diameter that carries the design flow, and then re-seats the inverts; it then makes a second,
> shorter pass from the outfall back upstream, seating each manhole onto the invert the first pass
> produced. Where constraints conflict it applies a published order of eight priorities, in which
> fitting existing structures and providing capacity outrank minimum cover, and maximum slope ranks
> last; maximum velocity and maximum cover are explicitly identified by Bentley as constraints that
> may be too limiting to enforce. The vendor states that the result "is intended only as a
> preliminary step" and that meeting every constraint is often impossible, placing final judgement
> with the engineer. The design basis is a steady-state GVF-Convex run; the dynamic solvers analyse
> only. Results are written to a separate, named alternative so that the input model is never
> overwritten.

---

*Research method: Bentley's LiveContent help was fetched as raw HTML and tag-stripped rather than
summarised, so the quotations above are the vendor's exact wording. The SewerCAD and SewerGEMS
copies of the Design Priorities page were diffed against each other to confirm the engine
description is shared. Bentley Communities forum threads and the Bentley/Virtuosity blog are
JavaScript-rendered and could not be read directly; none of the claims above depends on them.*
