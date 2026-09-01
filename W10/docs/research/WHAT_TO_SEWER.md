# What should actually be sewered?

Research note, 2026-09-01. Scripts `W10/py/research/r5`–`r9`; layers
`W10/shp/W10_marginal_branches.shp`, `W10_pipe_surplus.shp`, `W10_pipe_no_load.shp`;
figures `W10/img/research/`.

---

## Headline

**Between 117 km and 378 km of the 1,882.9 km design should not be built as gravity sewer —
6 % certainly, 20 % on a cost test the project cannot yet run.** The certain part is
**117.3 km that collects nothing and conveys nothing**: no load-bearing plot within 60 m of
it, and under 1 m³/d passing through it at saturation. The contingent part is
**48 settlements — 888 properties, 4,061 people, 830 m³/d, 1.1 % of the load — whose 65.8 km
of exclusive pipe costs 20 to 1,085 m per property against a network average of 13.8**, plus
the surplus conveyance that reaches them.

Two supporting numbers:

- **Depth breaches follow the emptiness.** 55 of the 239 breaches, and **832 m of the
  3,083 m of lift (27.0 %)**, sit on pipe with no load-bearing plot within 60 m. That is an
  independent confirmation of `OPTIMISATION.md`'s finding from the other direction.
- **The guideline's own size test does not settle this.** G201 p80 §8.1 defines a Remote
  Area as, among other things, under 500 residents or under 100 plots. Applied literally,
  **180 of the 187 settlements qualify** — because the cadastre fragments into one- and
  two-plot pieces — and those 180 hold 989 plots between them. The definition is not
  discriminating here. **The cost per property is.**

[Certain] on every measured figure. [Likely] on the recommendation, which needs unit rates
the project does not hold.

---

## The instrument, and why the flow threshold alone is not it

`OPTIMISATION.md` reported that dropping branches under 1 m³/d removes 333 km (18 %) for
0.2 % of the flow and 22 % of the pumping. Reproduced here on the same graph, same flow
tree, same load allocation, with the lift added:

| Drop branches under | pipe km | % of pipe | plots | properties | people | flow m³/d | % of flow | lift removed | % of lift | m per property |
|---|---|---|---|---|---|---|---|---|---|---|
| 0.5 m³/d | 311.8 | 16.6 | 771 | **0** | **0** | **0.0** | 0.00 | 242 m | 7.9 | — |
| **1.0** | **337.5** | **17.9** | 1,121 | 208 | 1,032 | 151.8 | **0.21** | 242 m | 7.9 | 1,623 |
| 2.0 | 422.6 | 22.4 | 2,551 | 1,584 | 8,277 | 1,169.6 | 1.59 | 290 m | 9.4 | 267 |
| 3.0 | 497.3 | 26.4 | 4,607 | 4,041 | 20,628 | 2,968.0 | 4.04 | 352 m | 11.4 | 123 |
| 5.0 | 613.9 | 32.6 | 8,611 | 9,447 | 47,400 | 6,954.4 | 9.47 | 401 m | 13.0 | 65 |
| 10.0 | 851.5 | 45.2 | 18,273 | 23,140 | 112,945 | 17,563.8 | 23.92 | 640 m | 20.8 | 37 |
| 20.0 | 1,069.7 | 56.8 | 30,328 | 41,993 | 198,824 | 31,998.8 | 43.57 | 827 m | 26.8 | 26 |

Whole network for comparison: 1,882.9 km, 62,615 plots, 97,076 properties, 73,442 m³/d —
**19.4 m per property, 25.6 m per m³/d.**

The first row is the striking one: **311.8 km of pipe whose accumulated flow at the upstream
end is under 0.5 m³/d, and which collects exactly nothing.** It reproduces the 333 km
headline (the small difference is the branch definition — see below).

**But that number cannot be used as it stands, and the reason matters.** Checking the
311.8 km against the cadastre: **48 % of it passes within 30 m of a plot that does carry
load.** The cause is the load allocation, not the pipe. Loads land on the nearest corridor
*node* within 160 m and nodes sit about 100 m apart, so a reach shows zero accumulated flow
at its upstream end while the houses along it drained into the node at the other end.

| No-load pipe within … of a load-bearing plot | 30 m | 60 m | 100 m | 160 m | 300 m |
|---|---|---|---|---|---|
| km | 149.5 | 178.7 | 209.2 | 230.0 | 263.3 |
| % of the 311.8 km | 48.0 | 57.3 | 67.1 | 73.8 | 84.4 |

**311.8 km is an upper bound, not a measurement.** The rest of this note uses a measure that
does not depend on the allocation at all.

---

## 1. Pipe with nothing on it — measured against the cadastre, not the tree

A reach is **surplus** when no load-bearing plot (56,414 of 64,071 records carry a load)
lies within a frontage distance of it. That is a statement about the pipe and the cadastre
only. The frontage distance is swept, because the answer moves with it:

| Frontage | 30 m | 45 m | **60 m** | 80 m | 100 m |
|---|---|---|---|---|---|
| Surplus reaches | 2,885 | 1,994 | **1,579** | 1,218 | 978 |
| Surplus km | 308.9 | 230.4 | **195.0** | 160.7 | 143.7 |
| % of the network | 16.4 | 12.2 | **10.4** | 8.5 | 7.6 |

60 m is the project's own `PLOT_SERVED_M`. **195.0 km — 10.4 % of the design — collects
nothing.**

Some of that is legitimate: a route from an outlying settlement to the works must cross open
ground. So cross it with the flow it carries:

| | km | % | Read as |
|---|---|---|---|
| Fronts plots, carries flow | 1,494.6 | 79.4 | normal sewer |
| Fronts plots, carries under 1 m³/d | 193.3 | 10.3 | the last reach to somebody's house — keep |
| **Collects nothing, conveys flow** | **77.7** | **4.1** | a real connector — keep, but it is a conveyance decision, not a collection one |
| **Collects nothing AND conveys nothing** | **117.3** | **6.2** | **surplus. Nothing fronts it and nothing flows through it** |

[Certain]. **117.3 km is the floor of this study** — the length that can be deleted with no
consequence whatsoever, before any economics.

Where it came from ties straight back to `CORRIDOR_QUALITY.md`:

| Corridor source | pipe km | removable km | % of that source | share of the removable |
|---|---|---|---|---|
| `auto_road` | 520.7 | **59.6** | **11.4 %** | **50.8 %** |
| `draft` | 911.8 | 30.4 | 3.3 % | 25.9 % |
| `auto_block` | 311.4 | 21.9 | 7.0 % | 18.7 % |
| `auto_link` | 92.2 | 4.7 | 5.1 % | 4.0 % |
| trunk / other | 46.8 | 0.7 | 1.5 % | 0.6 % |

**Half the removable pipe came from the road layer**, which holds 28 % of the length. The
road network reaches places the cadastre does not, and the design followed it there.

---

## 2. Who is each metre for?

The decisive attribution. A reach belongs **exclusively** to a settlement when every drop of
load upstream of it comes from that one settlement — its internal streets *plus* its spur
out, all the way to the chamber where its flow first mixes with somebody else's. That is
exactly what disappears if the settlement is not sewered.

Settlements are geometric: plots within 60 m of each other are one settlement. `VILLAGE_EN`
is blank on 43,557 of 61,272 plots and cannot carry the analysis. The 60 m grow distance was
swept, not chosen:

| Grow distance | 20 m | 30 m | 40 m | **60 m** | 80 m | 120 m |
|---|---|---|---|---|---|---|
| Clusters | 805 | 466 | 342 | **187** | 126 | 70 |
| Largest holds | 15.3 % | 21.4 % | 37.6 % | **80.4 %** | 81.2 % | **95.9 %** |

At 120 m the Ibri conurbation swallows everything and the outliers vanish; at 60 m it holds
80.4 % and the 12,584 plots outside it separate into settlements you can name.

**The whole network, attributed:**

| | km | % |
|---|---|---|
| Exclusive to one settlement | **1,365.7** | 72.5 |
| Shared between settlements (trunk and collectors) | 205.4 | 10.9 |
| **No load anywhere upstream** | **311.8** | 16.6 |

---

## 3. The marginal branches

At the 1 m³/d threshold the marginal network resolves into **1,889 separate branches**,
337.5 km, written to `W10/shp/W10_marginal_branches.shp` with length, plots, properties,
population, flow, lifting stations, lift, outlet coordinate and routed distance to the
works. What they serve:

| | branches | km | plots | properties | people | m³/d | lift | stations |
|---|---|---|---|---|---|---|---|---|
| **Serve nothing at all** | **1,681** | **287.7** | 691 | 0 | 0 | 0.0 | 219 m | 10 |
| Serve houses | 208 | 49.8 | 430 | 208 | 970 | 151.8 | 24 m | 2 |

The corridor source of the marginal pipe: `auto_road` 148.9 km (45.3 %), `auto_block`
85.4 km (26.0 %), `draft` 76.9 km (23.4 %), `auto_link` 17.5 km (5.3 %). **76.6 % of the
marginal network came from synthetic corridors, which are 45.9 % of the corridor network.**

**The most expensive pumping in the design is on branches that serve nothing.** The branches
carrying a lifting station, ranked by lift — every one of the top nine has zero properties:

| Branch | km | properties | m³/d | stations | lift | outlet ground | routed distance to works |
|---|---|---|---|---|---|---|---|
| 554 | 5.09 | **0** | 0.00 | 1 | **39.6 m** | 331.4 | 29.3 km |
| 1524 | 2.08 | **0** | 0.00 | 1 | 35.8 m | 385.1 | 35.8 km |
| 98 | 5.39 | **0** | 0.00 | 2 | 33.5 m | 386.3 | 29.9 km |
| 679 | 11.35 | **0** | 0.00 | 1 | 29.5 m | 324.9 | 37.0 km |
| 585 | 5.43 | **0** | 0.00 | 1 | 23.2 m | 416.8 | 77.8 km |
| 547 | 3.64 | **0** | 0.00 | 1 | 17.5 m | 323.4 | 32.3 km |
| 1485 | 0.21 | **0** | 0.00 | 1 | 13.4 m | 440.4 | 23.9 km |
| 294 | 1.90 | **0** | 0.00 | 1 | 13.2 m | 321.9 | 15.1 km |
| 943 | 2.52 | **0** | 0.00 | 1 | 13.1 m | 323.0 | 33.6 km |
| 645 | 0.50 | 1.0 | 0.74 | 1 | 12.9 m | 421.0 | 75.8 km |
| 821 | 2.70 | 1.0 | 0.74 | 1 | 10.6 m | 310.0 | 20.5 km |

The longest is **branch 679: 11.35 km of sewer and a 29.5 m lift, for nothing.** [Certain]

---

## 4. Cost-effectiveness — the metric, the distribution, and the break

**The metric: metres of exclusive pipe per property.** It is defensible because it is
additive (every metre belongs to exactly one settlement or to the shared trunk), it is
measured on the design itself rather than modelled, and it converts directly to money once a
per-metre rate exists. The companion is **metres per m³/d**, which matters when a settlement
has many plots and little load.

**Whole network: 1,365.7 km of exclusive pipe over 98,681 properties = 13.8 m per
property.** (The settlement table counts all 64,071 load records; the flow-tree table counts
the 97,076 properties whose load landed on a node within 160 m. The 1.6 % difference is the
allocation, and it does not move any conclusion.)

**The distribution across 187 settlements:**

| Exclusive m per property | settlements | plots | properties | people | m³/d | exclusive km |
|---|---|---|---|---|---|---|
| **under 20** | **106** | 63,231 | **97,793 (99.1 %)** | 432,070 | 73,871 | **1,299.9** |
| 20 – 40 | 8 | 469 | 547 | 2,667 | 466 | 14.5 |
| 40 – 80 | 9 | 102 | 122 | 587 | 92 | 6.5 |
| 80 – 150 | 8 | 106 | 80 | 422 | 62 | 10.7 |
| 150 – 400 | 17 | 147 | 124 | 315 | 195 | 22.7 |
| over 400 | 6 | 16 | 15 | 70 | 15 | 11.3 |
| no property at all | 33 | 45 | 0 | 0 | 0 | 0.0 |

**The break is at about 20 m per property, and it is a cliff rather than a slope.** 106
settlements sit below it and hold **99.1 % of the properties at 13.8 m each**; 48 settlements
sit above it and hold **0.9 % of the properties on 65.8 km of pipe**. The largest settlement
anywhere near the break is BAT at 17.6 m per property with 1,877 properties; the first
settlement above the break is a two-plot pocket at 20.0 m. So moving the cut between about
18 and 25 m per property changes the answer by a handful of properties either way, which is
what makes 20 a safe place to cut rather than an arbitrary one. It is not the only defensible
cut — 40 m per property would leave 8 more settlements and 547 properties inside the network
for 14.5 km — but every cut in that range is decided by the same 65.8 km.

The extreme tail: six settlements over 400 m per property hold **15 properties on 11.3 km**.
The worst is a single plot on 1.7 km — **1,085 m of sewer for one property.**

---

## 5. What the guidelines say

Read from the source PDFs in `Data/`. Page numbers are the printed folios, which for these
documents equal the PDF page index.

### The rule that governs — G201 §8, "Remote Areas & On-site Solutions", p80–84

> **p80 §8.1** "Remote Areas shall be defined as locations that meet **one or more** of the
> following criteria: ● Not connected to existing centralised water or wastewater networks
> ● Settlements located approximately **25 km or more** from existing centralized water or
> wastewater networks ● Communities with population **less than 500 residents or fewer than
> 100 plots** at the end of design period ● Areas with **geographical barriers preventing
> economical connection** to centralized systems"

> **p80 §8.2.1** "The primary objective for Remote Area solutions is to **optimize capital
> and operational expenditures** without compromising water quality and level of service to
> customers."

> **p83 §8.4.1** "Wastewater in Remote Areas shall be managed by one of the following
> methods: ● **Septic tanks** designed according to the Oman Private Sewage Disposal Code
> (OPSDC) ● **Holding tanks** designed for regular emptying by vacuum tankers ●
> **Decentralized compact treatment units (package plants)** for communities with a
> population between **50–5,000 inhabitants**." Plus: "Collection by vacuum tanker shall
> require the design of: ● Access routes suitable for vacuum tanker service ● Adequate
> turning radius at tanker emptying locations."

> **p83 §8.4.2** Package plants "shall be considered where: ● Communities are of sufficient
> size and density to justify a local centralised treatment plant … ● **Land is available**
> … ● **Skilled operations staff** can be provided or remote monitoring is feasible ●
> **Local reuse opportunities** exist for TSE ● **Access** is available to the necessary
> utilities".

> **p84** For small remote-area schemes: "**Energy consumption of approximately 0.8 kWh/m³**
> shall be assumed ● **Annual operations and maintenance costs estimated at 5 % of
> Investment CAPEX**."

### What settles a marginal case — G201 p96 §12.4

> "For the purposes of comparing alternatives, the period used is **25 years** … The **Net
> Present Value (NPV)** is applied to determine the lowest total lifetime cost at a given
> discount rate. Unless otherwise instructed by NWS, the **discount rate to be applied is
> 5 %**."

Which is the project's already-settled financial method (PROJECT-STATE §2, `T03_R01`), so no
new machinery is needed — only rates.

### The wastewater volume — PAM-GUD-203

| Page | Says |
|---|---|
| **p96 §10.5.1.6** | Package plants "are used to treat wastewater in **villages**, labor or military camps, **isolated residential communities** or resorts … These facilities typically serve populations **up to 5,000 inhabitants (approx. 750 m³/day)**" |
| **p101** | Constructed wetlands: HSSF 3–10 m²/PE, VF 1.2–5 m²/PE; "**only recommended to be applied in small STPs in rural areas (approximately up to 500 m³/day and/or 4000 PE)**" — a nature-based option for the outlying tranche, land permitting |
| **p56 §9** | Vacuum sewers suit "areas of **low-density population**, areas of flat terrain … where conventional gravity systems **may not be economical**", and "Implementation decisions must be supported by a comprehensive financial evaluation, **including the solution by tanker**, that considers both CAPEX and OPEX throughout the system's entire lifespan" — the guideline naming the tanker as the comparator |
| **p33** | "Where the **cost of excavation becomes prohibitive** the Engineer shall incorporate pumping stations into the design" — the same economic trigger, applied to depth |
| **p32 §4.6.1** | "Where main sewers are laid at considerable depths, it may be **more economical to lay shallow rider sewers** … and to connect the riders at a small number of convenient points" |
| **p17 §3** | "It is common practice on existing properties to install the PC chamber within the property immediately **upstream of the sewage holding (or septic) tank**" — the existing baseline in Ibri already *is* on-site |
| **p73, p68** | If a decentralised tranche is adopted, the works needs a **dedicated tanker discharge station** with screening, grit and FOG removal and a **flow equalisation tank**; septic loads are far stronger than network sewage (Table 31: BOD₅ 350–1,050, COD 1,350–5,000, TSS 900–4,300 mg/l) |

### The uncomfortable part

**The G201 p80 tests do not discriminate here.** Applied to the 187 geometric settlements:

| Test | Settlements caught | Plots | Properties | m³/d |
|---|---|---|---|---|
| Under 500 residents **or** under 100 plots | **180 of 187** | 989 | 970 | 853 |
| 25 km or more from the built network | **1** (a single plot at 25.4 km) | 1 | 1.5 | 1.1 |

The size test catches almost every settlement because the cadastre fragments into one- and
two-plot pieces, and the distance test catches almost none because Ibri wilayat is compact —
BAT, the furthest real settlement, is 22.5 km from the built network, just inside. [Certain]

So the operative criterion is the fourth one — *"geographical barriers preventing
**economical** connection"* — and the objective in §8.2.1, *"optimize capital and operational
expenditures"*. **The guideline hands the decision back to the economics, which is where the
project's own options doctrine already puts it.** The cost per property is the instrument;
the guideline supplies the menu of alternatives and the appraisal rules, not the cut-off.

---

## 6. Recommended tranches

| Tranche | Settlements | Plots | Properties | People | m³/d | % of load | Exclusive km | m/property | Recommendation |
|---|---|---|---|---|---|---|---|---|---|
| **0 — nothing to collect** | 33 | 45 | 0 | 0 | 0 | 0 | 0.0 | — | No property on them. Delete the pipe |
| **1 — sewer, core** | 1 | 51,487 | 81,706 | 358,925 | 61,672 | **82.6 %** | 1,052.7 | 12.9 | Conventional gravity. Not in question |
| **1 — sewer** | 105 | 11,699 | 16,087 | 73,145 | 12,199 | **16.3 %** | 247.2 | 15.4 | Connect |
| **2 — economics decide** | 17 | 571 | 669 | 3,254 | 558 | 0.75 % | 21.1 | 31.5 | Price against a package plant or tankered holding tanks |
| **3 — do not sewer** | 31 | 269 | 219 | 807 | 272 | 0.36 % | 44.7 | **204.2** | On-site. Do not extend the network |

Plus, outside the settlement attribution: **311.8 km with no load upstream, of which 117.3 km
neither collects nor conveys anything.**

### Tranche 1 — clearly worth sewering

**99.1 % of the properties and 98.9 % of the load, at 12.9–15.4 m of exclusive pipe per
property.** The large members are named settlements, not fragments:

| SID | Settlement | Plots | Properties | People | m³/d | Exclusive km | m/property | km to core | km to built network |
|---|---|---|---|---|---|---|---|---|---|
| 18 | AL TAYYEB (P.A.) — the Ibri conurbation | 51,487 | 81,706 | 358,925 | 61,672 | 1,052.7 | 12.9 | 0.0 | 0.0 |
| 116 | AL DIREZ | 8,918 | 12,570 | 56,870 | 9,488 | 201.0 | 16.0 | 0.1 | 13.3 |
| 165 | BAT (P.A.) | 1,501 | 1,877 | 8,202 | 1,479 | 33.0 | 17.6 | 7.0 | 22.5 |
| 19 | AL SEBEKHI | 454 | 676 | 3,162 | 504 | 6.9 | 10.2 | 0.0 | 7.4 |
| 184 | BAT (P.A.) east | 237 | 354 | 1,758 | 263 | 4.2 | 11.9 | 10.9 | 24.9 |

**Two of these are not simply "connect", and the design does not currently treat them as
options:**

- **AL DIREZ** is the west leg. `WEST_LEG.md` already establishes that it cannot reach the
  works by gravity — one saddle 11.93 m above its low point blocks every route — so it is
  pumped (≈14 m of lift, 6 km rising main) or it takes its own works. This note adds the
  scale: **12,570 properties, 9,488 m³/d, 201.0 km of exclusive pipe.** At 9,488 m³/d it is
  far past a package plant; it is a satellite STP.
- **BAT** (SIDs 165 + 184 + 182 together: 1,738 plots, 2,231 properties, 9,961 people,
  1,752 m³/d, 37.3 km of exclusive pipe) sits **7–11 km from the core and 22–25 km from the
  built network**. It passes the cost test comfortably at ~17 m per property, so the *local
  network* is worth building. What is not established is whether its flow should be conveyed
  10 km to the works or treated locally. **At 9,961 people and 1,752 m³/d it is above the
  package-plant ceiling** (G201 p83, G203 p96: 5,000 pe ≈ 750 m³/d) and above the
  constructed-wetland range (G203 p101: 500 m³/d / 4,000 PE), so the local option is a small
  conventional works. **This is a live options question and it is not in the W10 option set.**

### Tranche 2 — the economics decide (17 settlements, 21.1 km, 669 properties, 558 m³/d)

Package-plant eligible under G201 p83 (population 50–5,000):

| SID | Settlement | Plots | Properties | People | m³/d | Exclusive km | m/property |
|---|---|---|---|---|---|---|---|
| 64 | — | 229 | 271 | 1,214 | 253 | 6.97 | 25.7 |
| 136 | AL DARIZ (P.A.)-C | 75 | 101 | 519 | 83 | 2.44 | 24.3 |
| 36 | — | 67 | 67 | 356 | 50 | 2.29 | 34.2 |
| 40 | — | 57 | 57 | 303 | 42 | 1.43 | 25.1 |
| 176 | SWAIDA ALMA (P.A.) | 37 | 39 | 204 | 29 | 1.97 | 50.0 |
| 16 | — | 32 | 39 | 210 | 29 | 1.05 | 26.6 |
| 95 | — | 25 | 36 | 194 | 27 | 2.12 | 58.2 |
| 174 | — | 21 | 26 | 85 | 22 | 1.12 | 42.4 |

The remaining nine are under 50 people and fall to septic or holding tanks by G201 p83
regardless of the economics. **SID 64 is the one genuine borderline case**: 271 properties
and 253 m³/d at 25.7 m per property, only 0.25 km from the core envelope — cheap to connect,
easily large enough for a package plant. That one turns entirely on the NPV.

### Tranche 3 — do not sewer (31 settlements, 44.7 km, 219 properties, 272 m³/d)

**204 m of exclusive sewer per property, fifteen times the network average.** Worst cases:

| SID | Settlement | Plots | Properties | People | m³/d | Exclusive km | m/property | Solution |
|---|---|---|---|---|---|---|---|---|
| 26 | HAI AL SAADAH -S2 | 94 | 72 | 108 | 142 | 11.81 | 163.0 | package plant |
| 8 | ALSHARYAH | 10 | 7 | 39 | 5 | 6.41 | **880.5** | septic / tanker |
| 151 | — | 55 | 39 | 200 | 31 | 5.78 | 149.6 | package plant |
| 131 | — | 1 | 1.5 | 0 | 5 | 1.70 | **1,085.0** | septic / tanker |
| 14 | — | 4 | 6 | 11 | 4 | 1.68 | 261.1 | septic / tanker |

Twenty-eight of the thirty-one are under 50 people, so **G201 p83 puts them on septic tanks
to the OPSDC or on holding tanks emptied by vacuum tanker** — which, per G203 p17, is what
they already have.

---

## 7. Recommendation

1. **Delete the 117.3 km that collects nothing and conveys nothing.** No cost test needed,
   no property affected, no flow lost. Layer: `W10_pipe_surplus.shp`, `REMOVABLE = 1`.
   *This is a corridor problem, not a routing one — see `CORRIDOR_QUALITY.md`; half of it
   came from `auto_road`.*
2. **Do not sewer tranche 3.** 44.7 km, 219 properties, 0.36 % of the load, 204 m per
   property, on-site under G201 p83. Confirm with a site check that access exists for a
   vacuum tanker (G201 p83 requires suitable access routes and turning radii).
3. **Price tranche 2 before deciding** — 21.1 km, 669 properties, 0.75 % of the load. The
   comparison is a 25-year NPV at 5 % (G201 p96) of: gravity connection versus a package
   plant (0.8 kWh/m³, O&M at 5 % of CAPEX per G201 p84) versus tankered holding tanks. Eight
   of the seventeen are package-plant eligible.
4. **Add BAT as an option in its own right.** 2,231 properties, 1,752 m³/d, 22–25 km from the
   built network, above every decentralised ceiling in the guidelines. Conveyance versus a
   small satellite works is a genuine option and it is currently absent from the option set.
5. **Re-run the depth solve after 1 and 2.** 55 breaches and 832 m of lift (27.0 %) sit on
   surplus pipe. `OPTIMISATION.md` predicts about −22 % of the pumping from the 1 m³/d prune;
   this note supports that and gives the branches by name.
6. **If any decentralised tranche is adopted, size the tanker reception at the works.**
   G203 p73 requires a dedicated discharge station with screening, grit and FOG removal plus
   a flow equalisation tank; G203 p68 Table 31 gives the septic-load strengths to design it
   for. The total is small — 830 m³/d at most — but it is strong sewage, not dilute.

---

## What this does not settle

| | |
|---|---|
| **The money** | No unit rates exist yet. Every "economics decide" line needs the excavation, pipe, chamber and package-plant rates that `W9/analysis/W9_PIAD_financial_review.md` says are coming from Renardet's own cost data. Nothing here is priced |
| **Level of service** | This is a cost argument. Whether NWS will accept 219 properties left on septic tanks inside a sewered wilayat is a policy question, not an engineering one |
| **The load basis** | Everything scales with 1.456 properties per plot, measured on built plots and applied to planned ones. At 1.0 the saturation load is 54,602 m³/d rather than 74,675, and the marginal settlements move with it |
| **The 33 zero-property settlements** | 45 plots with no load at all. They may be genuinely vacant, or the land-use classification may be wrong about them. The GIS expert's clean data will say |
| **`auto_block` alignment** | 26 % of the marginal network sits on skeletonised corridors whose alignment is provisional (see `CORRIDOR_QUALITY.md` §6). If those corridors move, these lengths move |
| **Second-order pumping** | The lift figures here are the stations *inside* each branch. Removing a branch also changes depths downstream. Re-running the solve, not adding up columns, is what gives the real saving |

---

## Layers, figures, re-running

| Layer | Contents |
|---|---|
| `W10/shp/W10_marginal_branches.shp` | 1,889 branches at 1 m³/d: `KM PLOTS PROPS POP Q_M3D M_PER_PRP M_PER_M3D SERVES N_LIFT LIFT_M OUT_X OUT_Y OUT_Z ROUTE_KM VILLAGE` |
| `W10/shp/W10_pipe_surplus.shp` | every reach: `SRC DN LEN_M QADF_M3D D_LOAD SURPLUS REMOVABLE WADI_M DUAL_M PLOTIN_M` |
| `W10/shp/W10_pipe_no_load.shp` | the 311.8 km with no load upstream, with its distance to the nearest loaded plot |

| Figure | |
|---|---|
| `R_F4_surplus_pipe.png` | the surplus network, split into "collects nothing" and "collects and conveys nothing", with the 11 lifts over 20 m |
| `R_F5_cost_effectiveness.png` | the distribution by cost band, and the pruning trade-off |
| `R_F6_tranches.png` | 187 settlements coloured by tranche |

```
python W10/py/research/r5_marginal.py    # tree, branches, settlements, attribution
python W10/py/research/r6_tranches.py    # the break, the classification, the tranches
python W10/py/research/r7_surplus.py     # allocation-independent surplus
python W10/py/research/r8_pipe_defects.py
python W10/py/research/r9_figures.py
```

Records: `W10/run/r5_marginal_sweep.csv`, `r5_marginal_branches.csv`, `r5_settlements.csv`,
`r6_tranches.csv`, `r7_surplus_sweep.csv`, `r7_surplus_by_source.csv`, `r8_pipe_defects.csv`.
