# Can the lifting stations be reduced? — W10 optimisation study, 2026-09-01

You asked whether the design is the best possible version, and to investigate every way of
reducing the lifting stations while strictly following the design criteria. Ten strategies
were built and measured. The short answer is that **the layout is close to optimal, the
biggest lever available is forbidden by the guideline, and the station count is the wrong
thing to be optimising.**

## First, a correction to my own number

I reported **11** lifting stations. Measured consistently it is **21**. The 11 came from
double-filtering: the consolidated station layer had already been reduced to those with 50+
plots *within 750 m*, and the catchment test was then applied to the survivors. Everything
below runs one identical funnel and the base design comes out at 21:

> breaches → consolidate within 1.5 km (rule 9) → keep those whose **catchment** is 50
> properties or more (54 m³/d on the locked basis) → that is the station count

## Every strategy, measured the same way

| Strategy | Breaches | Clusters | **Stations** | Total lift | km > DN200 |
|---|---|---|---|---|---|
| **base** — smallest pipe at its own Table 11 minimum | 219 | 33 | **21** | 2,815 m | 194 |
| upsize to lay flatter | 184 | 38 | 25 | 2,327 m | 485 |
| climb penalty 100 | 218 | 36 | 23 | 2,815 m | 191 |
| climb penalty 1,000 | 207 | 33 | 21 | 2,683 m | 197 |
| climb penalty 2,500 | 206 | 40 | 28 | 2,665 m | 193 |
| climb penalty 6,000 | 210 | 39 | 27 | 2,717 m | 202 |
| avoid-list re-routing | 223 | 32 | 23 | 2,920 m | 187 |
| best routing + avoid + flatten | 201 | 33 | 22 | 2,544 m | 497 |
| route on depth gained @0.50 % | 222 | 34 | 21 | 2,849 m | 184 |
| route on depth gained @0.30 % | 209 | 37 | 24 | 2,718 m | 191 |

**Nothing beats the baseline.** The topography and the corridor set determine the answer;
the router does not.

## The big lever is prohibited

The obvious move was to upsize a run that is digging itself into the ground so it can be
laid flatter. Table 11 falls steeply with diameter — DN200 0.500 %, DN315 0.270 %,
DN400 0.205 % — and a 5 km run at 0.270 % instead of 0.500 % saves 11.5 m of depth. The
headroom is real: a reach carrying 7.7 L/s is being laid at 0.500 % when the tractive-force
floor is only 0.220 %.

It is not allowed. **PAM-GUD-203 p29 §4.3.1, read from the source and quoted in full:**

> "Sewers shall not be oversized to facilitate flatter slopes. Uniform slopes must be
> maintained between successive manholes."

One unqualified sentence, "shall not", no exception anywhere in the 201 pages. The reason is
on p167, listing the causes of hydrogen sulphide: *"a. Oversized lateral sewers and mains
resulting in low sewage velocity in sewers causing solids deposition and long retention
times, promoting anaerobic conditions"*, and p185 adds that *"Gravity sewers with very low
slopes are the ones with the greatest risk of H₂S formation"*. The move triggers both at
once, on long runs, at Omani temperatures.

The project already knew this. `TUTORIALS/T02` §6.3 carries the p29 prohibition and states
the consequence: *"the design has no choice but to accept the depth, and pump when the depth
runs out."* I built the optimiser without reading it. The script is kept as
`W10/py/p3_optimise.py` with a warning at the top rather than deleted.

Note what the prohibition does **not** say. It bans oversizing *for that purpose*. A pipe
may legitimately be large because the d/D cap, the 3 m/s limit or the ultimate-flow horizon
requires it, and the flatter Table 11 minimum then follows. The audit question is "what set
this diameter?" — and "the depth we wanted" fails it.

## The station count is the wrong objective

| Depth rule | Breaches | Clusters | Stations | Total lift |
|---|---|---|---|---|
| 12.0 m to invert (as coded) | 219 | 33 | 21 | 2,815 m |
| 12.0 m **cover**, as G203 p33 states | 204 | 35 | 24 | 2,706 m |
| **10.0 m cover** — stricter | 275 | 25 | **16** | 3,095 m |
| 14.0 m cover — information only | 144 | 35 | 23 | **2,247 m** |

A **stricter** limit gives **fewer** stations. Shallower breaches occur earlier and more
densely, so they consolidate into few clusters; a deeper limit makes them rare and
scattered, and each becomes a station of its own. Counting stations by distance-clustering
therefore measures breach density, not pumping need. **Total lift is the honest measure**,
and it ranks the other way — which is the physically correct order.

A related correction worth making regardless: the code tests ground minus **invert** against
12.00 m, while G203 p33 says **cover**, which is ground minus crown. The code has been
stricter than the guideline by one outside diameter on every reach — 0.30 m at DN200, 1.30 m
at DN1200. Measuring the quantity the guideline names is not a relaxation.

## What the guideline actually frames as the decision

G203 p33, verbatim:

> "The recommended maximum cover for sewer pipes is approximately 10 - 12m. Depths with
> cover greater than this shall be investigated with pipe manufacturers to identify any
> special requirements that may be necessary. **Where the cost of excavation becomes
> prohibitive** the Engineer shall incorporate pumping stations into the design."

So the trigger is **excavation cost**, and the limit is a recommended range, not a wall. The
project rule is a hard 12 m with no exemption, adopted after 21.3 m chambers passed a W6
audit — a good rule, and I am not relaxing it here. But the trade it forecloses is real and
it is exactly the 25-year NPV comparison the project's settled financial method already
runs. Going from 12 m to 14 m of cover is worth **20 % of the pumping** (2,815 → 2,247 m of
lift). **That is your decision, not mine**, and it needs the excavation and energy rates to
settle.

## Two real reductions, both decisions rather than optimisations

**1. The emptiest branches cost far more than they carry.**

| Drop branches under | Pipe | Flow lost | Breaches | Total lift |
|---|---|---|---|---|
| — | 1,883.6 km | — | 219 | 2,815 m |
| **1 m³/d** | 1,551.0 km (**−333**) | **151 m³/d (0.2 %)** | 174 | **2,200 m (−22 %)** |
| 3 m³/d | 1,396.2 km (−487) | 2,936 (4.0 %) | 154 | 1,938 m |
| 5 m³/d | 1,283.7 km (−600) | 6,865 (9.3 %) | 144 | 1,809 m (−36 %) |

**333 km of sewer to collect 151 m³/d** — 0.45 m³/d per kilometre. Those are the scattered
outlying settlements the skeletoniser reached. Both the guideline's economic trigger and the
project's options doctrine allow a decentralised answer for them, and it should be priced
before they are sewered.

**2. More treatment works does not help the pumping.**

| Scheme | Works | Breaches | Stations | Total lift |
|---|---|---|---|---|
| existing works only | 1 | 219 | 21 | 2,815 m |
| existing + west satellite | 2 | 216 | 21 | 2,797 m |
| existing + west + S6 | 3 | 222 | 21 | 2,875 m |
| existing + west + S6 + S10 | 4 | 222 | 21 | 2,864 m |
| five works | 5 | 214 | 24 | 2,758 m |

A clean negative result and a useful one for the options work: the pumping is caused by long
flat runs **inside** catchments, not by the distance to the plant, so a nearer works does not
remove it. Decentralisation has to be justified on conveyance cost, phasing and reuse
proximity — not on pumping.

## Is 21 too many?

| | Length | Stations | One per |
|---|---|---|---|
| NAMA built network (2006) | 111.6 km | 1 | 112 km |
| **W10 design** | **1,883.6 km** | **21** | **90 km** |
| W6 (guessed trunk, superseded) | 78.7 km | 4 | 20 km |

The design pumps **1.2× more densely than the network NAMA actually built**, over an area
4.8 times larger, reaching scattered settlements they never served. That is the strongest
evidence available that it is not over-pumped.

## Answer

**No further reduction is available inside the design criteria by changing the layout.** Ten
strategies were tested and none beat the baseline; the one that would have worked is
prohibited by name. What remains are three decisions, each of which needs a number I do not
have:

1. **Do not sewer the emptiest branches.** −22 % of the pumping for −0.2 % of the flow.
   Needs the cost of a decentralised alternative.
2. **Set the depth limit against excavation cost, as the guideline frames it.** 12 → 14 m of
   cover is −20 % of the pumping. Needs excavation and energy rates.
3. **Correct the depth measurement to cover rather than invert.** Free, and it is what the
   guideline says.

## Where it is

`W10/py/p3_variants.py` (the harness) · `p3_optimise.py` (withdrawn, kept with its warning) ·
`W10/run/p3_variants.csv`, `p3_depthcost.csv`, `p3_cover_rule.csv`, `p3_prune.csv`,
`p3_multiworks.csv` · `W10/docs/GRADIENT_CRITERIA_VERIFIED.md` for every criterion read back
from the source with its page.
