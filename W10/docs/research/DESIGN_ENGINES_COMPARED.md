# How the commercial tools actually design a gravity sewer — and what we should take from them

Research note, 2026-09-02, for the W11a design philosophy. No code was written and no design
number in this project changes as a result of it.

**The uncomfortable headline first: only one vendor of the four publishes its algorithm.**
Bentley publishes an ordered priority ladder and a numbered step list. Autodesk publishes
InfoDrainage's reach-level sizing routine but not its network-level behaviour. Innovyze
publishes InfoSewer's loop in prose. Civil 3D has no design engine at all in the sense we
mean — it has geometric rules and a separate HEC-22 resize command. Everything below that is
labelled [Guessing] is inference and should not be quoted as vendor behaviour.

**The second uncomfortable point: not one of these tools chooses the layout.** Every one of
them takes the network the engineer drew and sizes it. The hardest part of the Ibri problem —
which corridor, which hierarchy, which outfall — is unsupported by every commercial package
on the market. That means SewerGEMS can referee our hydraulics and can never referee our
layout.

---

## 1. Autodesk InfoDrainage

### 1.1 What it designs

Diameter (from a pipe size library), upstream and downstream invert or crown elevations,
hence slope and cover, and manhole sizes when enabled. It does **not** choose which pipes
exist or where they run: the Network Design Wizard's first step is *Select Flow Path*, i.e.
the engineer supplies the tree. [Certain] —
[Network Design](https://help.innovyze.com/display/infodrainage/Network+Design).

### 1.2 The criteria set

`Network Design Criteria` is an explicit, editable criteria form. The documented fields and
their exact wording: [Certain] —
[Network Design Criteria](https://help.innovyze.com/display/infodrainage/Network+Design+Criteria)

| Field | Verbatim description |
|---|---|
| Minimum Cover Depth | "The desired depth from the pipe crown/channel top to the cover elevation." |
| Minimum Slope | "The desired minimum slope for a pipe/channel. This is desirable when the ground is flat or is sloping away from the pipes and minimum slopes are required to reduce excavation." |
| Maximum Slope | "The desired maximum slope for a pipe/channel. This is desirable as laying connections too flat may result in blockages." |
| Minimum / Maximum Velocity | "The desired minimum velocity for a pipe/channel." / "…maximum velocity…" |
| Pipe Size Library | "The Pipe Size Library is a sequential list of pipe diameters." |
| Backdrop (Minimum) | "The desired minimum backdrop for a pair of connections, if a backdrop is below this, then it is lowered to 0." |
| Backdrop (Maximum) | "…if a backdrop is above this, then it is lowered to this value." |
| Design Level | Level Crowns (Soffits) or Level Inverts — how incoming and outgoing pipes are matched at a manhole. |

> Note the *Maximum Slope* description in the vendor's own help is self-contradictory — a
> maximum slope does not prevent laying pipes too flat. Treat it as an editorial defect in
> the help, not as a clue to behaviour. [Certain] that the text says this; [Guessing] as to
> what was meant.

Each criterion is a toggle: "When the option is turned on, the auto size calculation will
attempt to redesign the system and achieve the above cover where it is feasible." [Certain]

### 1.3 The one documented priority statement

There is **no published priority list**. There are exactly two documented statements from
which priority can be read, and no more:

1. Velocity yields to cover: "The program will attempt to select a size and slope with
   sufficient capacity that does not exceed the suggested velocity **but this may be broken
   to meet other criteria, such as cover depths**. In this case a warning is given at the end
   of the wizard." [Certain]
2. Cover yields to the downstream fixed point: on flat sites where the connection point is
   close to the surface, "it may not be possible to provide sufficient slope and sufficient
   cover further up the system. In this situation, **the minimum cover rule is broken, and a
   warning is provided**." — Autodesk on-demand training,
   [Designing pipes for no surcharge criteria](https://www.autodesk.com/learn/ondemand/curated/infodrainage-pipe-design/3E7qbETSVngHegFAjcM84o).
   [Likely] — this sentence was returned by search against the Autodesk learn page; the page
   itself refused a direct fetch, so I have not read it in situ.

So the readable order is: **capacity → downstream tie-in → cover → velocity**, with the last
two announced as warnings when broken. Anything beyond that is inference. [Likely]

### 1.4 The reach-level algorithm — this part *is* published

From [Auto Size Calculations](https://help.innovyze.com/display/infodrainage/Auto+Size+Calculations),
which is the most useful single page any of these vendors publishes. [Certain]

The routine "begins at the head of a Flow Path and progresses downstream through each
pipe/channel". Steps 1–5 accumulate area and base flow, set the initial size to the smallest
in the library, compute travel time as "the largest upstream time of concentration", read
rainfall intensity, and compute the flow. Step 6 is the sizing routine:

- **Initial elevations** — from minimum cover *and* the incoming pipes, so the pipe has
  "sufficient cover and align[s] to the lowest incoming crown/invert elevation based on the
  Design Level".
- **Slope range** — the criteria min/max slopes are intersected with the min/max slopes
  available for the candidate pipe sizes.
- **Search** — "The calculation starts from the flattest slope and seeks a diameter providing
  sufficient capacity for calculated flow and valid velocity."
- **Upsizing** — next size in the library; past the largest, "the program will continue based
  on the Additional Increment specified (75 mm by default) until sufficient capacity is
  reached".
- **Iteration within the reach** — "Once a solution is found, it's recorded and the
  calculation will make the pipe slightly steeper and repeat the check."
- **The objective** — "The solutions for different slopes are considered and **the one
  providing the minimum cover depth at the downstream end**, as well as meeting the velocity
  checks if applicable, will be selected."

That last sentence is the whole philosophy of the tool in one line: **among all feasible
(slope, diameter) pairs, take the one that leaves the trench shallowest at the downstream
end.** It is a greedy, purely local objective, and it is the same objective Bentley states in
prose ("minimize excavation").

Branch lines are sized identically and then aligned to the main line at the junction; a
backdrop is permitted if enabled, with the min/max rules above. Pipes and slopes can be
locked, and the help warns that locking slopes "is restrictive and is likely to lead to pipes
being deeper than necessary". [Certain]

### 1.5 Does it iterate?

- **Within a reach:** yes, explicitly — it enumerates slopes from flattest upward and keeps
  the shallowest-downstream feasible solution.
- **Along the network:** a single downstream sweep from the head of the flow path, with each
  reach tied to the lowest incoming level at its upstream node.
- **A reverse pass, relaxation, or revisiting upstream reaches after solving downstream:**
  **not documented anywhere I could find.** The audit/recalculate buttons in the reporting
  view re-check criteria; they are not described as re-solving. I will not claim InfoDrainage
  has no reverse pass — I will say Innovyze does not document one, and the shape of the
  published routine gives no place for one. [Certain] that it is undocumented; [Likely] that
  there is none.

### 1.6 Design criteria hierarchy in the UK sense

InfoDrainage frames design as two sequential criteria — **no-surcharge first, then no-flood**
— which is inherited practice from the Wallingford Procedure lineage
([Autodesk InfoDrainage Pipe Design module](https://www.autodesk.com/learn/ondemand/module/infodrainage-pipe-design)).
The Wallingford Procedure (HR Wallingford / Institute of Hydrology, 1981) shipped as WASSP
with six programs including **WASSP-OPT, the "Wallingford optimising method", and WASSP-COST,
a sewer system construction cost program** — i.e. the UK lineage had an explicit
cost-optimising design program forty-five years ago, and the modern descendant does not
expose one.
[Wallingford Procedure Vol 1](https://eprints.hrwallingford.com/37/1/Volume1_principles_methods_practice.pdf).
[Certain] on the program list; [Guessing] on any claim that InfoDrainage's engine descends
from WASSP-OPT specifically.

---

## 2. Autodesk Civil 3D pipe networks

### 2.1 It is not a design engine, it is a geometry rule engine

Civil 3D has **no flow input to its part rules**. The rules position pipes relative to a
surface and to structures; they never read a discharge. Sizing from flow is a separate
command (§2.4). [Certain]

The rule set —
[About Pipe Network Part Rules](https://help.autodesk.com/cloudhelp/2019/ENU/Civil3D-UserGuide/files/GUID-8600D35E-2B92-4377-88B4-C2FFED9950CC.htm):

**Pipe rules:** Cover and Slope · Cover Only · Length Check · Pipe to Pipe Match · Set Pipe
End Location.
**Structure rules:** Pipe Drop Across Structure · Maximum Pipe Size Check · Set Sump Depth.

### 2.2 The conflict resolution order — published, and short

From [About the Cover And Slope Pipe Rule](https://help.autodesk.com/cloudhelp/2021/ENU/Civil3D-UserGuide/files/GUID-39F96537-BBF1-4DAF-9CF0-8DC469C089F1.htm),
verbatim, in the order given: [Certain]

1. "The connections to structures are at a location as specified by the structure rules, if
   any are specified" — "with the first pipe having the highest precedence or priority".
2. "The pipe always slopes in the proper direction, with the minimum slope being honored,
   **unless this is in conflict with a connected structure**."
3. "The minimum cover is maintained **unless this is in conflict with a connected
   structure**."

And the tie-break between cover and slope: "When drawing a pipe, the pipe attempts to stay
within minimum and maximum cover values, unless the minimum or maximum slope is reached. At
that point, **maximum cover distance is exceeded to satisfy the minimum slope requirement**."

So: **structure rules beat slope; slope beats maximum cover; minimum cover is honoured
subject to the structures.** That is a genuine, published, three-level ladder — for geometry
only.

### 2.3 Local or propagating?

Local, with a one-directional sweep. The same page states the rule "applies to pipes starting
from upstream to downstream. A front pipe may cover a back pipe, though the rule applied to a
back pipe may cover the front pipe." Rules are applied as parts are created; on existing
parts they only re-run when *Apply Rules* is invoked — so a structure moved after layout
leaves stale geometry until the command is run.
[To Apply Rules to Parts in a Pipe Network](https://knowledge.autodesk.com/support/civil-3d/learn-explore/caas/CloudHelp/cloudhelp/2017/ENU/Civil3D-UserGuide/files/GUID-FD4D4D1F-50B8-4A02-91F8-43DFFF0EAE64-htm.html).
[Certain]

### 2.4 The one thing Civil 3D does that is design

*Analyze Gravity Network* → **Resize Pipes and Reset Inverts**, following FHWA **HEC-22**
(3rd edn), Section 7.5 energy grade line procedure. Documented limitations: the resize option
does not compute EGL/HGL; non-circular pipes are treated as circular using the inner width;
data-referenced networks can be computed but results cannot be applied; and **"the minimum
cover rule applies to all pipes except the most downstream pipe connected to the outfall"**.
[About Analyzing and Sizing a Gravity Pipe Network](https://help.autodesk.com/cloudhelp/2021/ENU/Civil3D-UserGuide/files/GUID-55DAEF71-2B5A-410E-9D60-DACA51306B2E.htm).
[Certain]

### 2.5 Positioning

Autodesk's own line is that Civil 3D's drainage tools are the InfoDrainage engine surfaced
inside Civil 3D, and that legacy Storm and Sanitary Analysis (which *did* do automated sizing
to velocity and cover criteria) is superseded.
[InfoDrainage vs SSA vs Drainage Analysis](https://www.autodesk.com/blogs/water/2025/04/09/autodesk-infodrainage-vs-ssa-vs-drainage-analysis-for-civil-3d/).
[Likely] — the blog refused a direct fetch; this is from the search index summary of it, not
from reading the page.

### 2.6 The critical separation Civil 3D gets right

**Maximum cover "provides validation purposes only and does not automatically reposition
parts. It simply produces a rule violation on the part if the specified value is exceeded."**
[Certain] Civil 3D distinguishes *rules that move geometry* from *checks that only flag*.
That distinction is worth more to us than anything else in the product.

---

## 3. Innovyze / Autodesk — InfoWorks ICM and InfoSewer

### 3.1 InfoWorks ICM: analysis for twenty years, design since 2027

ICM's identity is the simulation engine (full Saint-Venant, 1D/2D, real-time control). Design
was not part of it. **ICM Ultimate 2027** adds *Network Design*: "Network Design in InfoWorks
ICM Ultimate 2027 brings catchment-wide design into the same environment as analysis."
[Certain] — [Autodesk One Water blog, 7 Apr 2026](https://www.autodesk.com/blogs/water/2026/04/07/infoworks-icm-2027-network-design/)
(page refused direct fetch; text from search index) and
[Smart Water Magazine coverage](https://smartwatermagazine.com/news/autodesk-water/black-box-clarity-rethinking-network-design-infoworks-icm)
(fetched directly).

What is documented about the engine, verbatim from the Smart Water Magazine piece:

- "At the core of the new functionality is a **rule-based design engine**."
- "Engineers define constraints such as pipe diameters, slopes, velocities, and cover depths."
- "The software then **evaluates multiple design candidates and selects the optimal solution
  based on these criteria**."
- "The tool generates a comprehensive design report that explains every decision. Engineers
  can see **which pipe sizes were considered, why certain options were rejected**, and what
  factors governed the final slope or diameter."
- On cost: a webinar question about "linking the penalty system to real construction costs"
  drew the answer that "this idea is being actively considered" — i.e. **the ranking is a
  penalty function over criteria violations, and it is not a cost function**. [Likely]

Autodesk also states the practical split: site-scale (<~1,000 pipes) was InfoDrainage
territory, catchment-scale (>1,000–2,000 pipes) was ICM, and 2027 removes the round trip.
[Likely]

Layout: not described as chosen by the software anywhere I found. [Likely] it is not.

### 3.2 InfoSewer: a documented greedy downstream sweep

[Design in InfoSewer](https://help.innovyze.com/display/infosewer/Design+in+InfoSewer) is
explicit. [Certain]

- Two criteria sets are kept apart: "**Analysis criteria** which are used to determine the
  capacity of existing pipes" and "**design criteria** which are used to determine the size of
  new replacement pipes".
- "The design is carried out for **one pipe at a time** and it progresses **downwards along
  the flow direction**."
- Velocity: "InfoSewer makes sure that flow velocity in the designed pipes meet a
  user-specified minimum (e.g., not to be less than 2 ft/s…) and maximum (e.g., not to exceed
  10 ft/s…)."
- The failure ladder: "If the pipe fails to meet one or more design criteria, **pipe slope
  that satisfies all design criteria for the same pipe size would be searched for. If the pipe
  fails to meet all design criteria by changing slope alone, the model offers the option to
  change pipe size to the next large size defined.**"
- Drop manholes are introduced when velocity exceeds the maximum.
- Hard stop on failure: "**Pipes located to the downstream of a failed pipe will not be
  designed.**"
- Objective claimed: "InfoSewer designs existing pipes considering flow capacity constraints
  while minimizing cost."

Note the ordering: **slope is exhausted before diameter is increased.** That is the opposite
of the "upsize to lay flatter" move that W10 tested and PAM-GUD-203 p29 forbids — InfoSewer
raises the slope first and only enlarges when slope alone cannot pass. That is the correct
order for our guideline. [Certain] on the vendor text; [Likely] on the reading.

InfoSWMM Designer, a separate legacy product line, does use a genetic algorithm over slope,
size, storage, pumping and new piping. [Likely] —
[swmm5.org tutorial](https://swmm5.org/2020/08/17/infoswmm-designer-tutorial/). Not a
supported route for us.

---

## 4. Bentley SewerGEMS / SewerCAD — the reference point

Bentley is the only vendor here that publishes both an ordered priority ladder and a step
list, and it is why SewerGEMS is our referee.

### 4.1 The objective, stated

> "The design algorithm attempts to **minimize excavation, which is typically the most
> expensive part of installing sewer piping and structures**."
> — [Constraint Based Design](https://docs.bentley.com/LiveContent/web/Drainage%20and%20Utilities%20Help-v9/en/GUID-69F1E2898573473C8F90D56CA2DBE565.html) [Certain]

Same objective as InfoDrainage's "minimum cover depth at the downstream end", stated in
words instead of in the selection rule.

### 4.2 The priority ladder, in order

From [Design Priorities](https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-53684ACF09664DEEB80ADC7BAD949D9D.html):
[Certain]

1. A designed pipe should **fit within adjacent existing structures**.
2. A designed pipe should **not have a crown above an adjacent designed structure**.
3. **Pipe capacity should be greater than the discharge.**
4. **Downstream pipes should be at least as large as upstream pipes.**
5. **Pipe matching criteria downstream** should be met.
6. **Minimum cover constraint** should be met.
7. **Pipe matching criteria upstream** should be met.
8. **Maximum slope constraint** should be met.

And the honesty that goes with it: "higher design priorities, such as existing structure
locations and matching criteria, may prevent the minimum cover constraint from being met",
and "it is not always possible to meet every desired condition".

Tractive stress sits below the ladder: "**the maximum cover and maximum velocity are of more
priority than tractive stress if there are conflicts**" —
[Default Design Constraints](https://docs.bentley.com/LiveContent/web/Drainage%20and%20Utilities-v2024.1/Help/en/topics/1481550/GUID-55F371273E4D415C9B7CF8310AF7FA6B.html).
[Certain]

Is the priority editable? **No.** The constraint *values* are editable (Simple or Table, by
diameter); the *order* is fixed by the engine and not exposed. [Certain] that no setting is
documented; [Likely] that none exists.

### 4.3 It iterates in two passes — the mechanic worth stealing

The same Design Priorities page publishes the step list. **Upstream → downstream, 22 steps
per conduit**, of which the shape matters more than the detail:

| # | Step (abridged, verbatim wording preserved) |
|---|---|
| 1–2 | flow travel time, conduit discharge calculation |
| 3–4 | get conduit minimum size / maximum size |
| 5–6 | adjust **upstream** invert to match upstream **minimum cover**; then to match upstream structure (matchline offset) |
| 7–9 | adjust **downstream** invert to match downstream minimum cover; then **minimum slope**; then downstream fixed structure |
| 10–13 | adjust upstream invert to **maximum slope**, then fixed structure; re-adjust downstream to minimum slope, then fixed structure |
| 14 | **adjust conduit size for capacity to match discharge** |
| 15 | adjust downstream invert to match **minimum velocity** |
| 16–22 | re-run the whole geometric block (matchline, cover, max slope, fixed structures, min slope) after the size changed |

Then, explicitly: "**After designing all pipes from upstream to downstream, we design all
pipes from downstream to upstream.**" The reverse pass is four steps: adjust downstream
structure elevation to the conduit downstream invert; adjust conduit downstream invert to
fixed structure; adjust conduit upstream invert to maximum slope; adjust conduit upstream
invert to fixed structure. [Certain]

Three things to read out of that list:

1. **Geometry is set before capacity, then re-set after** (steps 5–13, then 14, then 16–22).
   The engine does not size and then place; it places, sizes, and re-places.
2. **Every constraint is applied as a monotone "adjust to match" operator**, not as a solve.
   Later operators can undo earlier ones — which is exactly why an ordered ladder is needed
   to say who wins.
3. **The reverse pass exists to lift structures to the inverts the forward pass produced.**
   It is a reconciliation pass, not a re-optimisation.

### 4.4 What it does not do

It does not choose layout, it does not choose pumping-station locations, and it does not
evaluate cost. "Minimise excavation" is a proxy for cost, applied reach by reach. [Certain]

---

## 5. The comparison that matters

| | **InfoDrainage** | **Civil 3D pipe networks** | **InfoWorks ICM 2027** | **InfoSewer** | **SewerGEMS / SewerCAD** |
|---|---|---|---|---|---|
| **Does it design?** | Yes — diameter, inverts, slope, cover, manhole size | Rules position geometry only; separate HEC-22 *Resize Pipes and Reset Inverts* | Yes, since Ultimate 2027 (new) | Yes — size and slope | Yes — conduit size, node inverts, inlets |
| **(a) What is optimised** | Shallowest trench: "the one providing the minimum cover depth at the downstream end" | Nothing. Rules satisfy constraints in a fixed order; no objective | A **penalty score** over criteria; explicitly *not* construction cost (yet) | "minimizing cost", not further defined | "minimize excavation, which is typically the most expensive part" |
| **(b) Rule priority** | Not published. Two documented yields: velocity yields to cover; cover yields to the downstream tie-in | Published, 3 levels: structure rules > minimum slope > maximum cover; max cover is a *flag*, not a mover | Not published beyond "constraints" | Implicit: capacity → try slope at same size → then next size up | **Published, 8 levels, fixed and not user-editable**; tractive stress below max cover and max velocity |
| **(c) Iteration** | Within a reach: enumerate slopes flattest-first, keep shallowest-downstream feasible. Network: one downstream sweep. **No reverse pass documented** | One-directional upstream→downstream at layout; re-run only via *Apply Rules* | "evaluates multiple design candidates" — mechanism unpublished | One pipe at a time downstream; slope search then size step; **stops the whole downstream branch on failure** | **22-step forward pass per conduit, then a 4-step reverse pass over the whole network** |
| **(d) Who chooses layout** | Engineer (*Select Flow Path*) | Engineer | Engineer [Likely] | Engineer | Engineer |
| **Infeasibility reporting** | Warning at end of wizard; orange cells; warning triangle on the offending value | Rule violation marker on the part | Design report naming rejected candidates and the governing factor | Downstream of a failed pipe is left undesigned | Documented as unavoidable: "it is not always possible to meet every desired condition" |
| **Algorithm published?** | Reach-level yes, network-level no | Rules yes, no algorithm to publish | No | Prose description only | **Yes, in full** |

**The convergent answer across four independent vendors:** the objective is *minimum
excavation / shallowest trench*, the method is a *greedy downstream sweep with a local search
over (slope, diameter)*, and the layout is *always the engineer's*. Nobody ships a global
optimiser. [Certain]

---

## 6. What the optimisation literature says

### 6.1 The standard formulation

The sewer network design (SND) problem is a highly constrained **mixed-integer non-linear
program**, treated as NP-hard, and is universally decomposed into two sub-problems:
**layout selection (LS)** and **hydraulic design (HD)**. Duque, Duque, Aguilar & Saldarriaga
(2020), *Water* 12(12):3337, state it cleanly: [Certain]

> "The layout of a sewer network defines the flow direction within the network following a
> tree-like structure where all manholes are connected to the outfall through a unique path.
> Given a layout, a hydraulic design establishes the diameter for each pipe and the invert
> elevation of its two endpoints."

The objective function that essentially everybody uses, in the form given by de Villiers, van
Rooyen & Middendorf (2017), *J. South African Institution of Civil Engineering* 59(3), after
Moeini & Afshar (2012): [Certain]

```
Minimise  C = Σ(i=0..N) Li · Ki(di, Ei_ave)  +  Σ(j=0..M) Kj(hj)
```

- `Li` — length of pipe *i*
- `Ki` — **unit cost of pipe i as a function of its diameter `di` AND its average cover depth
  `Ei_ave`** — this is where excavation enters
- `Kj` — unit cost of manhole *j* as a function of its height `hj`
- `N`, `M` — number of pipes, number of manholes

**Consensus on the objective function:** minimise total installed capital cost, expressed as
pipe cost driven jointly by diameter and mean cover depth, plus manhole cost driven by depth.
Pumping, where included, adds construction plus energy terms. Excavation is *never* a separate
term — it is inside the pipe unit cost as a function of depth, which is why "minimise
excavation" and "minimise cost" collapse into the same thing for a fixed layout. [Certain]

**The dissent worth recording:** practice states the objective differently. WEF MOP FD-5 /
ASCE MOP 60 §6.1: *"The objective of design is to provide a sewer system at the **lowest
annual cost** compatible with its function, while providing sufficient durability for the
design period."* Annual, not capital. The academic literature almost never optimises life-cycle
cost; the manual of practice does. [Certain]

### 6.2 Can layout and sizing be separated?

**This is the one question the literature genuinely disagrees on, and both sides are explicit.**

*Against separation* — de Villiers, van Rooyen & Middendorf (2018), JSAICE:

> "The two sub-problems of the optimisation are strongly linked — for each layout a unique set
> of hydraulic parameters exists. Consequently, if an optimal design is to be found, the
> sub-problems have to be solved simultaneously."

*For separation, with the price named* — Duque et al. (2020):

> "The predominant approach to solve the problem considers the layout selection (LS) and
> hydraulic design (HD) as independent (and subsequent) problems. **This separation allows for
> tractability of the problem at the price of design optimality.**"

And Lejano (2006), as reported by de Villiers et al.: because simultaneous optimisation is so
expensive, "most research has been done on the hydraulic optimisation sub-problem, while the
layout remains static."

**The consensus, stated honestly:** separation is *theoretically wrong and practically
universal*. Every author who separates says so and quantifies the loss; every author who
couples them pays a computational cost that scales badly. The mature position, and the one
Duque et al. adopt, is a **third way: separate the two problems but let the layout stage use a
cost surrogate that is refined by feedback from the hydraulic stage.** Their scheme runs a
mixed-integer program for layout, a shortest-path dynamic program for hydraulics, then
regresses realised design cost onto layout decisions to update the surrogate, "significantly
reducing the optimality burden that arises from decoupling the problems." [Certain]

The surrogates used for the layout stage are worth knowing, because choosing one is a real
decision:

| Surrogate for layout cost | Author |
|---|---|
| Pipe length only (minimum spanning tree, Kruskal) | Navin et al. |
| Ground cutting cost, linear in invert elevations, plus constant £/m | Hsie et al. (Steiner minimal tree via MIP) |
| Linear function of flow direction and flow rate, **refined every iteration** | Duque et al. (2020) |

### 6.3 The method lineage, with names and years

| Method | Authors and year |
|---|---|
| Dynamic programming for optimal sewerage | Argaman, Shamir & Spivak (1973), *Proc. ASCE Env. Eng. Div.* 99(EE5):703–716 |
| DP / DDDP for branched sewer cost design | Mays & Yen (1975), *Water Resour. Res.* 11(1):37–47 |
| Serial DDDP for multi-level branching systems | Mays & Wenzel (1976), *Water Resour. Res.* 12(5):913–917 |
| **Layout *and* design together** | Mays, Wenzel & Liebman (1976), *J. Water Resour. Plan. Manage. Div.* 102(2):385–405 |
| DP for optimal layout (position of manholes along the trunk, branch connection order) | Walters (1985), *Eng. Optim.* 9:37–50 |
| Shortest-path spanning tree for layout + DDDP for inverts, layout improved by a search-direction method | Li & Matthew (1990) |
| Deterministic vs stochastic layout models | Diogo & Graveto (2006), *J. Hydraul. Eng.* 132(9):927–943 |
| GA + quadratic programming | Pan & Kao (2009) |
| ACO + tree-growing algorithm for simultaneous layout and size | Moeini & Afshar (2012, 2013); slopes by NLP/BFGS in the 2017 extension |
| Adaptive GA | Haghighi & Bakhshipour (2012) |
| Loop-by-loop cutting algorithm to generate feasible layouts | Haghighi (2013), *JWRPM* 139(6) |
| Tabu search + loop-by-loop cutting, layout and hydraulics | Haghighi & Bakhshipour (2015) |
| Cellular automata, two-phase simulation–optimisation with SWMM | Zaheri et al. (2020) |
| Iterative MIP (layout) + shortest-path DP (hydraulics) with a learned cost surrogate | Duque, Duque, Aguilar & Saldarriaga (2020), *Water* 12(12):3337 |

Known weakness of the DP family, stated by Duque et al.: "A DP approach suffers from the
problem of dimensionality in its application in the design of sewer systems." The graph /
shortest-path reformulation is the standard escape. [Certain]

### 6.4 Excavation depth versus pumping — the finding that matters most to Ibri

**Li & Matthew (1990)** solved the hydraulic design with DDDP *including online pump stations*
and concluded that **the optimum is where excavation depth and the number of online pumping
stations are balanced**; further, **relaxing the maximum excavation depth constraint reduces
the number of pumping stations**, and where excavation is not excessive it is preferable to
allow more excavation than to add a pump station. [Likely] — this is reported consistently in
the recent literature (e.g. the 2024 *Urban Water Journal* paper on series of pipes with
pumping stations for flat terrains); I have not read Li & Matthew in the original.

Also from that line of work: in flat terrain pumping is not optional, and pumping cost is a
significant fraction of total scheme cost, so a design method that treats a pumping station as
a binary failure of the gravity design will get the economics wrong. [Likely]

**This directly corroborates `W10/docs/OPTIMISATION.md`.** The W10 measurement — that a *stricter*
12 m→10 m cover limit produced *fewer* clustered stations but *more* total lift (16 stations /
3,095 m against 24 / 2,706 m), and a 14 m limit produced the least lift of all (2,247 m) — is
the same relationship Li & Matthew found. It also confirms the W10 conclusion that **station
count is the wrong objective and total lift is the honest one**, because count is an artefact
of how breaches cluster while lift is in the cost function.

---

## 7. Constructability rules from the adoption standards

Sources read in full from the source PDFs, not from memory:

- **Ten States Standards** — *Recommended Standards for Wastewater Facilities*, 2014 edition,
  Chapter 30, §§33–34.
  [PDF](https://www.health.state.mn.us/communities/environment/water/docs/tenstates/tenstatestan2014.pdf)
- **WEF MOP FD-5 / ASCE MOP 60** — *Gravity Sanitary Sewer Design and Construction*, 2nd edn
  2007, Chapters 5 and 6.
  [PDF](https://sanihub.info/wp-content/uploads/2024/01/ASCE-gravity-sanitary-sewer-design-and-construction-2007.pdf)
- **Water UK DCG** — *Sewerage Sector Guidance Appendix C, Design and Construction Guidance*,
  Approved Version 2.2, 29 June 2022, Parts B4–B7.
  [PDF](https://www.water.org.uk/sites/default/files/2023-04/SSG%20Appendix%20C%20-%20Design%20and%20Construction%20Guidance%20v2-2.pdf)
- **Sewers for Adoption 7th edn** — superseded in England by the DCG above; still current for
  Wales. I could not obtain a fetchable copy, so **every SfA7 figure below is second-hand and
  tagged accordingly.**

### 7.1 The rules, side by side

| Rule | Ten States (2014) | ASCE MOP 60 / WEF FD-5 (2007) | Water UK DCG (2022) |
|---|---|---|---|
| **Minimum public sewer size** | §33.1 "A public gravity sewer conveying raw wastewater **shall not be less than 8 inches (200 mm)** in diameter." | 8 in (200 mm) used throughout as the base case; no separate prohibition found | B6.1 "100 mm nominal internal diameter for ten properties or less; or **150 mm** … for more than ten properties" |
| **Maximum manhole spacing** | §34.1 **≤400 ft (120 m)** for ≤15 in; **500 ft (150 m)** for 18–30 in; up to 600 ft (185 m) with adequate modern cleaning equipment | §6.4 same figures, plus "Greater spacing, **up to 1,000 ft (300 m)**, may be acceptable in larger sewers" | B5.2.6 **90 m** manhole-to-manhole; **45 m** where either node is an inspection chamber |
| **Where a chamber is mandatory** | §34.1 "at the **end of each line**; at all **changes in grade, size, or alignment**; at all **intersections**" | §6.4 "at the junctions … and at any change in grade, pipe size, or alignment, except in curved alignments"; terminal manhole at the upper end, in the ROW | B5.2.3 at every change of alignment or gradient; **at the head of all branches**; at every junction of two or more public sewers; wherever the size changes; at each lateral's upstream end |
| **Straight between chambers** | §33.5 "sewers 24 inches (600 mm) or less **shall be laid with straight alignment between manholes**. Straight alignment shall be checked by either using a laser beam or lamping." Curvilinear only >600 mm, "limited to **simple curves that start and end at manholes**", with the minimum slope increased to hold 2 fps | §6.5 curved sewers accepted for large diameters and endorsed for economy — "eliminating manholes needed at each abrupt change of direction"; "Inspection and maintenance requirements generally determine minimum diameters of curved sewers" | B4.2 "Sewers and lateral drains **should be laid in straight lines in both the vertical alignment (profile) and horizontal alignment (plan)** unless agreed with the sewerage company" |
| **Uniform slope between chambers** | §33.44 "**Sewers shall be laid with uniform slope between manholes.**" | implicit in the reach-based method of §5.6 | implicit |
| **Change of direction at a chamber** | §34.4 curved flow channels require the minimum slope to be increased | §6.5 the reason curves exist is to avoid a manhole per abrupt change | B5.2.26 "The channel **should not bend by more than 90 degrees** (including any connecting pipe)"; swept channels required |
| **Drop / backdrop trigger** | §34.2 "A drop pipe **shall** be provided for a sewer entering a manhole at an elevation of **24 inches (610 mm) or more** above the manhole invert"; outside drop, fully concrete-encased; below 610 mm the invert is filleted | drop manholes used where working space demands | B5.2.27 "**Steeper gradients are preferred to the use of backdrops.** … Where steeper gradients are impractical, backdrops should be constructed … **Ramped backdrops should be used for manholes rather than vertical backdrops**" |
| **Branch soffit matching** | §33.6 for a size change "place the 0.8 depth point of both sewers at the same elevation" | §6.14 the computation form reserves lines for transition losses and invert drops | B5.2.25 ≤3 properties onto ≤150 mm: **soffits level**; otherwise branch soffit no lower than the main and **invert ≥50 mm above** the main invert |
| **Self-cleansing** | §33.41 mean full-pipe velocity **≥2.0 fps (0.6 m/s)**, Manning n = 0.013; **≥3.0 fps (0.9 m/s)** for ≥48 in | §5.5.3 "ASCE and WEF now advocate a transition to the **tractive force approach**"; §6.9 traditional 2 fps min, ~10 fps max | B6.9 **0.75 m/s at one-third design flow**; if unattainable, DN150 at not flatter than **1:150** with ≥10 dwellings, or DN100 at 1:80 (1:40 with no WC) |
| **Depth of flow at design** | §33.42 reduced slope permitted where depth ≥ **0.3 D** at average flow, with written maintenance assurance | §6.9 traditionally half-full to 15 in and three-quarters above, but "engineers are encouraged to … design for a full pipe when capacity determines the pipe slope" | B3.1.4 foul sewers "**no more than 75 % of pipe full**" |
| **No oversizing to flatten** | §33.43 "**Flatter slopes shall not be justified with oversize sewers.**" | §5.6.2 the self-cleansing slope, where steeper, *becomes* the design slope — the reach is then "controlled by self-cleansing rather than by capacity" | not stated in these terms |
| **Minimum cover** | §33.2 deep enough to serve basements and prevent freezing (no number) | §6.8 no single method; rules of thumb 1 m below basement floor, 1.8 m below foundation top; 3.6 m+ in commercial districts | B5.1.7 to pipe crown: **0.35 m** gardens/paths, **0.5 m** height-restricted driveways, **0.9 m** mews and open space, **1.2 m** other highways |
| **Maximum depth** | not set | §6.1 "excessive depths increase construction costs" — economic, not a limit | B5.2.10–11 standard manhole details to **6 m** cover-to-soffit; beyond 6 m "the details should be agreed in advance with the sewerage company" |
| **High-velocity protection** | §33.45 >10 fps (3 m/s) needs scour/displacement protection; §33.46 anchors on ≥20 % grades at 11 / 7.3 / 4.9 m centres | §6.9 >10 fps tolerable with attention to material, abrasion, turbulence, thrust | — |

### 7.2 The three rules every one of them shares

1. **A chamber at every change of direction, gradient, or size, at every junction, and at the
   head of every branch.** Ten States §34.1, MOP 60 §6.4, DCG B5.2.3. Unanimous, and it is a
   *topology* rule, not a hydraulics rule.
2. **Straight and uniform between chambers**, with curves as a deliberate, size-gated
   exception. Ten States §33.5 + §33.44, DCG B4.2, MOP 60 §6.5.
3. **A hard cap on chamber spacing set by cleaning equipment reach**, not by hydraulics:
   90 m (UK) / 120 m (US ≤375 mm), stretched only when the operator's equipment justifies it.
   MOP 60 §6.4 says so outright: "this must be coordinated with the capabilities of the
   utility's cleaning equipment."

### 7.3 What none of them says — stated as a gap, not filled by inference

**No adoption standard I read prohibits dead ends or short branches.** [Certain] I searched
all three documents for it. What they do instead is *price* them: every head of branch needs
an adopted access structure (DCG B5.2.3b), every line end needs a manhole (Ten States §34.1),
and cleanouts may not substitute for a manhole nor be used at the end of a lateral longer than
150 ft / 45 m (Ten States §34.1). DCG B5.2.5 comes closest to relief: "**no access is required
at a node if it connects less than three properties and there already is, or will be,
sufficient access to carry out sewer maintenance.**"

So the discipline against fragmented layouts in the standards is economic, not prohibitive:
short branches are allowed and each one costs a chamber. Any rule we write against
short branches is *our* rule, and must be justified on cost, not cited to a standard.

### 7.4 The hand method the manuals actually prescribe

MOP 60 §5.6 is the canonical reach-level procedure and is worth having in front of us, because
it is a **maximum of three slopes**: [Certain]

> §5.6.1 "The pipe slope necessary to go from the upstream invert depth to the minimum depth at
> the next manhole is then calculated and compared to the necessary pipe slope for capacity.
> **The steeper of the two slopes is selected at this point.** Other sizes may be considered for
> the reach, as reasonable, with each size being identified with its slope."
>
> §5.6.2 "After a diameter and its slope for capacity are determined for a reach, the slope
> needs to be checked to determine whether a steeper slope is required for self-cleansing. If
> it is, **the self-cleansing slope becomes the design pipe slope** and the reach is controlled
> by self-cleansing rather than by capacity or sewer minimum invert depth constraints."

And on convergence, §6.14: "**Several trial designs may be required to determine which one will
properly distribute the available hydraulic head.**"

---

## 8. What our philosophy should take from each

Ordered by how much it would have changed W10.

### 8.1 Take Bentley's two-pass structure — this is the single biggest gap in W10

W10 ran one downstream sweep and published what fell out. SewerGEMS runs a **forward pass that
places, sizes, and then re-places** (steps 5–13, 14, 16–22) and then a **reverse pass that
reconciles structures to the inverts the forward pass produced**. InfoDrainage has the forward
half and no reverse half. We should have both, and the reverse pass is cheap: it is four
operations, not a re-solve.

Concretely for W11a: after the downstream sizing sweep, a reverse sweep that (a) lifts every
chamber to the invert actually achieved, (b) re-checks maximum slope, (c) re-applies the fixed
points (existing STP invert, existing manholes, the Main Pipe tie-in). W10's 45.92 km below
minimum cover is exactly the class of defect a reverse reconciliation pass surfaces.

### 8.2 Take the published, ordered priority ladder — and publish ours

Bentley's eight-level ladder is the model. Ours is not the same ladder, because our constraints
differ (no oversizing to flatten; 12 m cover; dual carriageway exclusion), but it must be
**written down, ordered, and fixed** so that when two rules collide the answer is
deterministic and auditable rather than an accident of code order. W11a P1 says the auditor is
written first; the ladder is what the auditor arbitrates.

A first cut of our ladder, to be argued rather than adopted:

1. Fixed existing points (STP invert, existing manholes, Main Pipe tie-in) — never moved.
2. Corridor legality (no pipe along a dual carriageway) — a hard exclusion, not a penalty.
3. Capacity: `Q_capacity ≥ Q_ultimate` at the d/D cap.
4. Downstream pipe ≥ upstream pipe.
5. Table 11 minimum gradient **for the diameter actually laid** — the W10 defect was storing
   the gradient for a different diameter than the one written out.
6. Minimum cover.
7. Chamber spacing (Table 12) — currently violated on 64.8 % of length.
8. Maximum cover (12 m) — and when it breaks, that is a pumping decision, not a failure.
9. Maximum velocity / scour.

### 8.3 Take Civil 3D's separation of movers from flags

**"Maximum cover … simply produces a rule violation on the part if the specified value is
exceeded"** — it does not move anything. Every constraint in our engine must be declared as
either a *mover* (it changes geometry) or a *flag* (it only reports). W8's 50-blocking /
9-reporting split is the same idea and W11a already inherits it; what Civil 3D adds is that
the *engine* knows the difference, not just the audit. A constraint that is a flag must not be
allowed to silently move a pipe, and a constraint that is a mover must never be reported as
"passed" when it moved something else to get there.

### 8.4 Take MOP 60's max-of-three slope rule as the reach primitive

`S_design = max(S_capacity, S_min_cover_to_next_chamber, S_self_cleansing)` — and, because
PAM-GUD-203 p29 forbids oversizing to flatten, **that is the whole rule**. It is also exactly
what Ten States §33.43 backs: "Flatter slopes shall not be justified with oversize sewers." We
now have two independent adoption standards saying the same thing as our project guideline,
which upgrades the W10 finding from "the guideline says so" to "this is the international
position."

### 8.5 Take InfoSewer's failure ladder, and its stopping behaviour

Slope is exhausted at the current diameter **before** the diameter is increased. Under our
no-oversizing rule that ordering is not merely sensible, it is mandatory: the only legitimate
reasons to increase a diameter are capacity, the d/D cap, and the maximum velocity — never
depth. Every reach should record *which of those three set the diameter*, and the auditor
should reject any reach whose recorded reason is "depth".

InfoSewer also refuses to design downstream of a failed pipe. That is a defensible design
decision and we should make ours explicitly: W10 silently carried on past failures, which is
why 2.80 km of surcharged trunk shipped.

### 8.6 Take ICM 2027's design report — it is P2 with a trace

"Engineers can see which pipe sizes were considered, why certain options were rejected, and
what factors governed the final slope or diameter." That is precisely W11a P2 (one function per
published number) extended one step: not only *what* the number is, but *what it beat*. For
each reach we should persist `DIA_SET_BY`, `SLOPE_SET_BY`, and the rejected candidates. The
cost is a few columns; the benefit is that "why is this pipe DN400?" stops being a research
project.

### 8.7 Take InfoDrainage's local objective, and know its limit

"The one providing the minimum cover depth at the downstream end" is the right *local*
objective given that we cannot trade diameter against depth. But it is greedy: it optimises
each reach against the next node with no view of the 5 km of trunk downstream. W10's ten
routing strategies all landed within 21–28 stations and none beat the baseline, which is the
empirical signature of exactly this — **the topography and the corridor set determine the
answer, and a smarter local rule does not move it.** Do not spend W11a effort on a better local
search. Spend it on the auditor and the chamber layer.

### 8.8 From the literature: accept the two-stage decomposition, and say what it costs

Duque et al. (2020) name the trade honestly: separating layout from sizing buys tractability
"at the price of design optimality". De Villiers et al. (2018) say the sub-problems "have to be
solved simultaneously" for a true optimum. **We separate.** The report should say so in one
sentence and give the reason: the layout is not free to vary, because corridors are roads,
dual carriageways are excluded, and the trunk is an input. Our layout stage is constrained to
the point where it is nearly determined — which is the strongest possible justification for
decoupling, and it should be stated rather than assumed.

If we ever want the third way, Duque's mechanism is the cheap one: run the sizing stage, regress
realised cost onto layout choices, and use the fitted surrogate to re-pick the layout. That is a
W12 idea, not a W11a one.

### 8.9 From the literature: fix the objective function before optimising anything

The academic objective is capital cost, with excavation *inside* the pipe unit cost as a
function of mean cover depth. The manual-of-practice objective is **lowest annual cost** (MOP 60
§6.1). Ours, per the settled options doctrine in PROJECT-STATE §2, is NPV over 25 years at 5 %.
Those are three different objectives and they rank designs differently. The one thing all three
agree on is that **station count is not an objective** — which is what `W10/docs/OPTIMISATION.md`
concluded from measurement, and Li & Matthew (1990) concluded from theory forty years ago: the
optimum is a *balance* between excavation depth and number of pumping stations, and relaxing
the depth cap reduces station count. Total lift, and ultimately NPV, are the honest measures.

### 8.10 From the adoption standards: the chamber is the unit, and the standards agree unanimously

W11a P4 already says this. The standards make it non-negotiable and give the numbers:

- A chamber at **every change of direction, gradient or size, every junction, and the head of
  every branch** (all three standards).
- **Straight and uniform between chambers** (Ten States §33.5, §33.44; DCG B4.2).
- Spacing capped by cleaning-equipment reach: our G203 Table 12 sits in the same band as the
  90 m UK and 120 m US figures. W10's 6,541 m longest reach is not a marginal exceedance of a
  local rule — it is outside every adoption standard in the English-speaking world by a factor
  of fifty.
- **No drop unless a steeper gradient is genuinely impractical** (DCG B5.2.27), and where one is
  needed, ramped rather than vertical, triggered at ≥610 mm (Ten States §34.2).
- **Branch soffit no lower than the main, invert ≥50 mm above the main invert** (DCG B5.2.25) —
  a cheap, checkable junction rule W10 never applied.

And the one place we must *not* cite a standard: **there is no adoption rule against dead ends
or short branches.** If W11a penalises them, it does so on cost, and it says so.

---

## 9. Source register

Read directly and quoted:

- InfoDrainage — [Network Design Criteria](https://help.innovyze.com/display/infodrainage/Network+Design+Criteria) · [Network Design](https://help.innovyze.com/display/infodrainage/Network+Design) · [Auto Size Calculations](https://help.innovyze.com/display/infodrainage/Auto+Size+Calculations) · [Metric Tutorial Ch.3](https://help.innovyze.com/display/infodrainage2021v1/Metric+Tutorial+Chapter+3+-+Defining+Flow+Paths+and+Pipe+Design)
- Civil 3D — [Cover And Slope Pipe Rule](https://help.autodesk.com/cloudhelp/2021/ENU/Civil3D-UserGuide/files/GUID-39F96537-BBF1-4DAF-9CF0-8DC469C089F1.htm) · [Pipe Network Part Rules](https://help.autodesk.com/cloudhelp/2019/ENU/Civil3D-UserGuide/files/GUID-8600D35E-2B92-4377-88B4-C2FFED9950CC.htm) · [Analyzing and Sizing a Gravity Pipe Network](https://help.autodesk.com/cloudhelp/2021/ENU/Civil3D-UserGuide/files/GUID-55DAEF71-2B5A-410E-9D60-DACA51306B2E.htm) · [Length Check Pipe Rule](https://knowledge.autodesk.com/support/civil-3d/learn-explore/caas/CloudHelp/cloudhelp/2021/ENU/Civil3D-UserGuide/files/GUID-E2EB9556-2908-413F-8251-0E27B4B54128-htm.html)
- InfoSewer — [Design in InfoSewer](https://help.innovyze.com/display/infosewer/Design+in+InfoSewer)
- InfoWorks ICM — [Smart Water Magazine, network design](https://smartwatermagazine.com/news/autodesk-water/black-box-clarity-rethinking-network-design-infoworks-icm)
- Bentley — [Design Priorities](https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20SS5-v2/en/GUID-53684ACF09664DEEB80ADC7BAD949D9D.html) · [Constraint Based Design](https://docs.bentley.com/LiveContent/web/Drainage%20and%20Utilities%20Help-v9/en/GUID-69F1E2898573473C8F90D56CA2DBE565.html) · [Using Automatic Constraint Based Design](https://docs.bentley.com/LiveContent/web/Bentley%20SewerGEMS%20Help%20SS5-v2/en/GUID-73F4F92E-4F53-4962-98DA-096CED12833B.html) · [Default Design Constraints](https://docs.bentley.com/LiveContent/web/Drainage%20and%20Utilities-v2024.1/Help/en/topics/1481550/GUID-55F371273E4D415C9B7CF8310AF7FA6B.html)
- Standards — [Ten States Standards 2014](https://www.health.state.mn.us/communities/environment/water/docs/tenstates/tenstatestan2014.pdf) · [ASCE MOP 60 / WEF FD-5 (2007)](https://sanihub.info/wp-content/uploads/2024/01/ASCE-gravity-sanitary-sewer-design-and-construction-2007.pdf) · [Water UK DCG v2.2 (2022)](https://www.water.org.uk/sites/default/files/2023-04/SSG%20Appendix%20C%20-%20Design%20and%20Construction%20Guidance%20v2-2.pdf)
- Literature — [Duque, Duque, Aguilar & Saldarriaga (2020), *Water* 12(12):3337](https://www.mdpi.com/2073-4441/12/12/3337) · [de Villiers, van Rooyen & Middendorf (2017), JSAICE 59(3)](https://www.scielo.org.za/pdf/jsaice/v59n3/06.pdf) · [de Villiers, van Rooyen & Middendorf (2018), JSAICE — ACO layout](https://scielo.org.za/scielo.php?script=sci_arttext&pid=S1021-20192018000300001) · [Wallingford Procedure Vol 1 (1981)](https://eprints.hrwallingford.com/37/1/Volume1_principles_methods_practice.pdf)

Could not be fetched (403/paywalled) — anything attributed to these is tagged [Likely] and came
from a search-index summary, not from reading the page:

- Autodesk One Water blog posts on InfoWorks ICM 2027 Network Design and on InfoDrainage vs SSA
- Autodesk on-demand learning pages under `autodesk.com/learn/ondemand`
- Sewers for Adoption 7th edition (all editions)
- Water UK DCG 2021 edition (the 2022 v2.2 was obtained instead and is the one quoted)
- Li & Matthew (1990) in the original; Mays and Mays & Wenzel papers in the original — cited
  from the citing literature, not read
