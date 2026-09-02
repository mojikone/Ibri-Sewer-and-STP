# When is a lifting station cheaper than a deeper trench?

**Research + measurement, 2026-09-02. Nothing here is designed; nothing upstream is modified.**

G203-p33 §4.6.3 states the decision and gives no number. Read from the source PDF, not
recalled:

> "The recommended maximum cover for sewer pipes is approximately 10 - 12m. Depths with
> cover greater than this shall be investigated with pipe manufacturers to identify any
> special requirements that may be necessary. **Where the cost of excavation becomes
> prohibitive the Engineer shall incorporate pumping stations into the design.**"

So "12 m" is a recommendation about *cover* and about *pipe strength*; the station trigger
is an economic test the guideline leaves to us. This document builds that test.

---

## 0. The three things worth knowing

**1. The premise this study was commissioned on is a misreading of a column, and it inverts.**
`W10/run/p3_lookahead.csv`'s `recover_m` was read as "how far downstream the depth recovers
below 12 m", giving 115 of 239 within 100 m and all within 3 km. Reconstructed exactly on
the design's own graph and gradients, that column is numerically the **distance at which
the un-stationed pipe passes 12.00 m again** — how far a station can be *deferred*, not how
quickly the depth recovers. 159 of the 226 rows match my independently computed deferral
distance to the metre. Under the correct reading, **226 of 239 breaches cannot be dug
through at all**: delete the station and the pipe is over 12 m again a median of 115 m
later. Only **13** ever rejoin the design profile.

**2. Of those 13, ten are cheaper to dig through than to pump — and two of them are the
largest stations in the design.** Node 2933 carries 36,974 plots and 42,754 m³/d and
breaches by **3 mm**; node 8543 carries 16,368 plots. Dropping the ten avoids 2.84 MOMR of
station present value for 1.34 MOMR of extra excavation, a **net 1.50 MOMR** on provisional
rates. But at the consolidated level project rule 9 works on — 1.5 km clustering — **all 30
clusters keep a station**, because no cluster is made entirely of eliminable breaches.

**3. The number that decides is not the excavation rate. It is whether NWS's manning rule
applies.** On NWS's own PIAD basis (1,000 OMR/month per pumping station) the present value
of manning is **169,127 OMR per station — 86 % of the median station's whole life-cycle
cost**. Pumping *energy* is 0.4 % of operating cost (median 49 OMR/yr). Move the manning
assumption and the answer moves from 10 breaches droppable to 2. Move the excavation rate
across its entire published range, 10 to 90 OMR/m/m, and it moves only from 11 to 4. **Get the
station O&M establishment settled with NWS before spending another day on excavation
rates.**

---

# PART A — the cost relationship, from sources

## A1. Three published functional forms, and they do not agree

| Form | Equation (as published) | Depth exponent | Source |
|---|---|---|---|
| **Linear** | cost/m = (m_α·d + n_α)·h + (m_β·d + n_β), with m_α = 110 USD/m³, n_α = 127 USD/m², m_β = 1,200 USD/m², n_β = −35 USD/m; d = diameter (m), h = average excavation depth (m) | **1.0** | Maurer, Wolfram & Herlyn (2010), reproduced verbatim as eq. 4 of [Duque et al., *Urban Water Journal* 2024](https://www.tandfonline.com/doi/full/10.1080/1573062X.2024.2329086) |
| **Power ≈1.5** | K_p = 1.93·e^(3.43·d) + 0.812·Ē^1.53 + 0.437·Ē^1.47·d ; manhole K_m = 41.46·h_m | **1.47 – 1.53** | Mansouri & Khanjani (1999), *J. Water Wastewater* 10:20–30 (Persian), Kerman City; quoted as eq. 16–18 in [Appl. Sci. 15(9):4836, 2025](https://www.mdpi.com/2076-3417/15/9/4836) |
| **Quadratic** | earthwork = w·L·(c_e·d + c_r·d²/2); sheeting/shoring = 2·L·(c_s·d + c_rs·d²/2); pipe = k_m·D^m | **2.0** | Swamee & Sharma formulation; parameter sets published as k_m = 8,561, m = 1.478, c_e = 126.1 Rs/m³, c_r = 6.24 Rs/m⁴, c_s = 185.5 Rs/m², c_rs = 19.08 Rs/m²/m, k_h = 12,440 Rs/m ([IRF Goa 2014](https://www.digitalxplore.org/up_proc/pdf/73-1399966324120-125.pdf)) and k_m = 7,894, m = 1.394, c_e = 31.7, c_r = 62.994, c_s = 220.48, c_rs = 14.133, k_h = 13,663 ([IJMSERH](https://ijmserh.com/admin/img/25_Design.pdf)) |

[Certain] on the quotations — each was pulled from the text of the paper, not from memory.
[Likely] on which one is right for Ibri: **none of them, until the BoQs arrive.** The
literature genuinely disagrees on whether trench cost is linear, 1.5-power or quadratic in
depth, and the disagreement is not cosmetic: over 4 → 12 m the marginal cost of depth rises
by 1.0×, 1.7× and 3.0× respectively.

Two structural points that all three share and that matter more than the exponent:

- **Diameter is the cheap variable, depth is the expensive one.** Swamee's pipe term is
  D^1.39–1.48 and the earthwork term is where the depth non-linearity lives; Maurer's depth
  coefficient (110·d + 127) is dominated by the constant, so at DN200 the depth term is
  149 USD/m per metre of depth against a diameter-driven base of 205 USD/m.
- **The classic "cost = a·D^b·d^c" separable form does not appear in any of the modern
  fitted work.** Every published fit is additive — a diameter term plus a depth term plus a
  manhole term — because the physical processes are additive. The nearest thing to a
  published exponent on diameter alone is Tyteca (1976), *b* = 1.2 to 1.5 (cited in [EPA,
  *Costs of Urban Stormwater Control Practices*](https://www.winslamm.net/assets/files/classes/StormwaterManagement/Microsoft%20Word%20-%20M4e2%20Costs%20of%20Urban%20Stormwater%20Control%20Practices%20Aug%2031%20200.pdf)).

## A2. Two empirical depth-banded rate tables — and the fact that they stop at 5 m

**Central Coast Council (NSW) Southern Region DSP 2019 v2.0, Appendix I**, gravity sewer
mains, AUD/m, 2019/20 ([source PDF](https://cdn.centralcoast.nsw.gov.au/sites/default/files/Plan_and_build/Plumbing_and_sewage/DSP_-_South_-_Appendix_I_Valuation_of_Existing_and_Proposed_Assets.pdf)):

| DN | Min depth | 1.5–3 m | 3–4.5 m | > 4.5 m | marginal, mid-band (AUD/m per m) |
|---|---|---|---|---|---|
| 225 | 413 | 511 | 647 | 790 | 91 → 95 |
| 300 | 560 | 645 | 814 | 942 | 113 → 85 |
| 375 | 716 | 838 | 978 | 1,117 | 93 → 93 |
| 450 | 905 | 1,018 | 1,172 | 1,300 | 103 → 85 |
| 525 | 1,091 | 1,091 | 1,363 | 1,506 | 181 → 95 |
| 600 | 1,263 | 1,373 | 1,555 | 1,688 | 121 → 89 |
| 750 | 1,105 | 1,814 | 1,938 | 2,071 | 83 → 89 |

Rising mains, same source, AUD/m: DN100 368 · DN150 423 · DN200 459 · DN225 479 · DN250 513
· DN300 586 · DN375 714 · DN450 842 · DN600 1,473. The same appendix carries a *Sewage
Pumping Station Cost Curve* with axes to 1,300 L/s and AUD 7,000,000 — the curve itself is a
graphic and its values could not be read.

**US EPA-430/9-81-003, *Construction Costs for Municipal Wastewater Conveyance Systems
1973–1979*, Table 4.3**, bare-in-place cost USD/linear foot, normalised to Kansas City MO,
1st quarter 1979, from ~11,593 bid items over 777 projects
([NEPIS](https://nepis.epa.gov/Exe/ZyPURL.cgi?Dockey=00000K3N.TXT)):

| Dia (in) | < 8 ft | 8–15 ft | > 15 ft | marginal shallow → deep (USD/ft per ft) |
|---|---|---|---|---|
| 8 | 17.18 | 21.14 | 33.75 | 0.72 → 1.94 |
| 10 | 17.41 | 20.53 | 38.50 | 0.57 → 2.77 |
| 12 | 22.27 | 23.15 | 40.66 | 0.16 → 2.69 |
| 15 | 22.67 | 27.35 | 50.33 | 0.85 → 3.54 |
| 18 | 31.14 | 33.88 | 47.53 | 0.50 → 2.10 |
| 21 | 35.51 | 49.57 | 63.86 | 2.56 → 2.20 |
| 24 | 42.74 | 45.48 | 61.23 | 0.50 → 2.42 |
| 30 | 61.39 | 63.49 | 74.29 | 0.38 → 1.66 |
| 36 | 91.55 | 78.68 | 99.71 | −2.34 → 3.24 |

[Likely] on these values: they were extracted by the fetcher from the NEPIS OCR text and I
could not pull the raw text a second way to re-verify them digit by digit. The **pattern**
is what matters and it is unambiguous — on **seven of the nine diameters** the marginal cost per unit of depth
rises by a factor of 2.7 to 17 once the trench passes 15 ft (4.6 m). The 21 in row falls
(2.56 -> 2.20) and the 36 in row has a negative shallow marginal, so both are noise.

**The finding neither table can hide: no published depth-banded rate table goes deeper than
about 5 m.** Central Coast's last band is "> 4.5 m", EPA's is "> 15 ft". Our excursions run
from 12 m to 57 m. Every number quoted below at 12 m and beyond is an **extrapolation of two
to three times the range of the data**, and that, not the choice of exponent, is the honest
statement of uncertainty.

## A3. Where the method changes — the steps in the curve

| Depth | What changes | Source |
|---|---|---|
| **1.52 m (5 ft)** | Protection becomes mandatory: shield, shoring or sloping | [OSHA 1926 Subpart P, as summarised by Cornell EHS](https://ehs.cornell.edu/campus-health-safety/occupational-safety/excavations/excavations-shield-and-shoring) |
| **~2 m (urban road reserve)** | Microtunnelling already beats open cut where reinstatement is expensive — reinstatement is put at ~70 % of an open-cut project's direct cost | [Utility Magazine](https://utilitymagazine.com.au/what-factors-make-microtunnelling-more-cost-effective-than-traditional-open-cut-methods/) |
| **~4.5–4.6 m** | The last band of every published rate table. EPA's marginal cost triples above it | above |
| **~5 m (greenfield)** | Microtunnelling break-even in open country | Utility Magazine, above |
| **~6 m** | Standard trench boxes run out; beyond this it is engineered support | [ESC Pile](https://www.escpile.com/trench-shield) |
| **6.1 m (20 ft)** | OSHA requires a registered professional engineer to design the protective system | Cornell EHS, above |
| **6.0 – 10.0 m** | "The maximum sewer depth is generally considered between 6.0 to 10.0 m" — the constraint sewer-optimisation papers actually impose | [IRF Goa 2014](https://www.digitalxplore.org/up_proc/pdf/73-1399966324120-125.pdf) §III(e) |
| **10 – 12 m cover** | G203-p33 recommendation; pipe manufacturer to be consulted beyond | G203-p33 §4.6.3 |

**The step at 6 m is the one that should worry us.** Above it, cost stops being a rate per
cubic metre and becomes a design problem: a PE-designed support system, then sheet piling or
a heading. There is no reason to expect any smooth function fitted on 1.5–4.5 m data to
carry to 12 m, and the fact that our design routinely lays pipe at 10–12 m — with 57 m as
the extreme — deserves a line in the report on its own.

## A4. Lifting station cost

**Capital.** The only large, modern, published regression for wastewater pumping stations:

> **ln C_T = 4.3189 + 0.5329 · ln P_e** — 360 Portuguese stations, contracts 2005–2015
> restated in 2016 €, C_T in k€, P_e = total hydraulic power in kW = γQH with γ = 9.81 kN/m³.
> Cabral, Marchionni, Covas et al., ["Statistical modelling of wastewater pumping stations
> costs", WDSA/CCWI 2018](https://ojs.library.queensu.ca/index.php/wdsa-ccw/article/download/12264/7860/22989)

Duque et al. (2024) code the same relation as C_c = e^4.3184 · P^0.5329 · (1000 €/k€) ·
(1.1 USD/€). Sample range: flow 3–1,329 L/s, head 3–83 m; Type I compact stations 0.5–14 kW,
Type II 0.5–70 kW, Type III 5–350 kW. Cost rises with coastal location and with the number
of pump groups.

**Cross-check.** EPA-430/9-81-003 fits **Cost = 1.59 × 10³ · q^0.59** (q in gpm, 1979 USD).
Two datasets forty years and a continent apart, and the scale exponent is 0.53 against 0.59.
[Certain] that pumping stations show strong economies of scale; a station is roughly a
**square-root** function of its duty, so two small stations cost about 1.4 times one station
of twice the duty.

**Operating cost.** Duque et al.: C_o = (1/η)·C_e·t·f_o·P. Our own doctrine (PROJECT-STATE
§2 item 1f) requires OPEX bottom-up from duty, so energy is computed as
E = 2.725 × 10⁻³ · V · H / η kWh, V the annual volume pumped in m³. Everything else comes
from NWS's own PIAD rule set (`W9/analysis/W9_PIAD_financial_review.md` §2.2): staff
1,000 OMR/month **per pumping station**, power 0.01–0.03 OMR/kWh with 0.02 adopted, M&E
maintenance 1.0 %/yr of M&E capital, insurance 1.0 %/yr.

## A5. What the literature itself concludes about the depth limit

- Li & Matthew (1990): "the optimal design resulted when a **balance between excavation
  depth and the number of on-line pumping stations** was achieved" — the trade-off has been
  the recognised formulation for 35 years, and nobody publishes a universal depth.
- Duque et al. (2024), relaxing their own maximum depth from 5 m to 6 m on 20-pipe series:
  "**the cost of increasing excavation depth is less than the cost of adding a pumping
  station**", and "fewer pumping stations are needed when the maximum excavation depth
  constraint is relaxed, suggesting that when excavation is not excessive, it is preferable
  to allow more excavation than to add a pump station."
- Same paper: pumping stations are **20 % to 95 % of the total cost** of the series they
  appear in; the correlation of total cost with pump **power** is 0.99 and with pump **head**
  only 0.72. "What increases the most the total cost in series with pumping is not the
  number of pumps but rather their power requirement."
- And the finding most directly aimed at how W10 places stations: the optimal solutions
  "**do not place the pumping at the end of the series, as is normally done in practice, but
  place it upstream in order to reduce the pumping flow rate.**"

[Likely] The literature's practical answer, then, is a range of **5 to 10 m**, it is set by
constructability rather than by a computed optimum, and the profession's own optimisers put
stations **upstream where the flow is small**, not at the first node that trips a depth rule.

---

# PART B — our own numbers

## B1. The reconstruction, and how it is verified

`W10/py/research/r10_depth_vs_pumping.py` rebuilds the design network with the pipeline's
own machinery — `netlib.load_network`, `p1_subnetworks.flow_tree`, `p2_sizing.size_all`,
`p3_breach_diag.solve_with_gov` — and reproduces **239 of 239 breaches with lift heights
differing from `W10_lift_sized.shp` by at most 0.005 m.** It is the same run.

The counterfactual is exact, not approximate. Downstream of a breach *b*, with the station
deleted:

> **invert_noPS[m] = min( invert_shipped[m], invert_noPS[prev] − s·L )**

The shipped invert at *m* is already the minimum over the minimum-cover cap and every
upstream branch **with** the station in place. Deleting the station adds exactly one deeper
candidate — the continuation of *b*'s own branch — and `min` is monotone, so this single
line reproduces a full network re-solve along that path.

The measured quantity is the **excursion depth-metre integral**

> **DM = ∫ (depth_noPS − depth_withPS) dL   [m²]**

which is the extra trench the deep option buys. Multiply by a marginal excavation rate in
OMR per metre of trench per metre of depth and you have the cost of digging through.

## B2. The premise does not survive the reconstruction

Walking each of the 239 excursions downstream until either the profiles rejoin or the pipe
passes 12.00 m again:

| Outcome | n |
|---|---:|
| **REBREACH** — the pipe is over 12 m again; the station is *deferred*, not saved | **226** |
| **CONVERGED** — the pipe rejoins the design profile; the station can be *eliminated* | **13** |

Deferral distances for the 226: median **115 m**, p25 41 m, p75 310 m, p90 639 m, max
2,824 m. That distribution is the one that was read as "recovery". On a nearest-depth join,
**159 of the 226 `recover_m` values equal my deferral distance to the metre**, and the
median absolute difference across the class is **0.0 m**. [Certain] on my own numbers, which
are reproducible from the script; [Likely] that `recover_m` was computed as a deferral
distance, since I could not read the script that produced it (it is not in the repository
and its node ids, running to 57,987, belong to a different graph build than the 20,965-node
design graph).

The weaker measure — "how far until the *ground alone* has fallen by (depth − 12.00 m)",
ignoring that the pipe keeps falling at 0.3–0.5 % — clears only **18 of 239 within 100 m,
36 within 500 m and 49 within 3 km**. So the optimistic reading fails on that basis too.

**Why the terrain cannot rescue these.** For a pipe at 12 m to return to 1.6 m cover over a
length L, the ground must fall by 10.4 m **plus** s·L. At DN200's 0.500 % over 500 m that is
12.9 m of ground fall in 500 m — a 2.6 % average grade. Ibri does not have it. The 12 m
excursions are not local humps; they are the terrain.

## B3. The 13 that could be eliminated, ranked by the rate at which the decision flips

`K_FLIP` is the marginal excavation rate, in OMR per metre of trench per metre of depth, at
which digging and pumping cost the same. It is rate-free, so it survives every cost
assumption we do not yet have. The plausible band from the published tables is **15–60**.

| NODE | depth m | plots up | Qadf m³/d | excursion m | DM m² | dig OMR (b=1.5) | station PV OMR | **K_FLIP** | verdict at 30 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 39032 | 14.51 | 0 | 0.1 | 330 | 286 | 11,532 | 176,327 | **459** | dig |
| 38181 | 13.47 | 17 | 26 | 54 | 321 | 14,727 | 180,978 | **369** | dig |
| 39100 | 12.60 | 1 | 1.3 | 695 | 665 | 25,336 | 176,332 | **209** | dig |
| 28221 | 13.66 | 8 | 7.7 | 235 | 1,332 | 57,422 | 176,366 | **92** | dig |
| 44722 | 12.76 | 24 | 23 | 768 | 1,734 | 66,908 | 179,820 | **81** | dig |
| **2933** | **12.003** | **36,974** | **42,754** | 1,208 | 6,438 | 279,448 | **739,962** | **79** | **dig** |
| 44 | 13.26 | 16 | 13 | 370 | 2,156 | 98,500 | 177,081 | **54** | dig |
| **8543** | 13.04 | **16,368** | **18,115** | 2,500 | 7,302 | 331,302 | **525,220** | **48** | **dig** |
| 6642 | 13.52 | 48 | 77 | 1,190 | 3,825 | 142,935 | 190,417 | **40** | dig |
| 491 | 13.38 | 3,212 | 3,558 | 1,806 | 7,466 | 311,995 | 313,583 | **30.2** | *knife edge* |
| 24927 | 12.58 | 1,021 | 1,359 | 3,087 | 14,475 | 599,569 | 253,081 | **12.7** | pump |
| 21187 | 17.79 | 0 | 1.6 | 1,444 | 11,689 | 597,175 | 176,337 | **8.9** | pump |
| 18921 | 13.13 | 5,959 | 6,136 | 5,539 | 29,946 | 1,288,038 | 360,877 | **8.4** | pump |

Six have K_FLIP > 60 — **dig, whatever the rate turns out to be**. Three have K_FLIP < 15 —
**pump, whatever the rate turns out to be**. Four sit inside the band and need real rates.

**Node 2933 is the case that should be quoted in the report.** It carries 36,974 plots and
42,754 m³/d, it exceeds 12.000 m by **3 millimetres**, and the current rule answers that by
building the second-largest lifting station in the design — 85 kW, 336 kOMR of capital,
740 kOMR of life-cycle cost — where 279 kOMR of extra excavation over 1.2 km would do. Node
8543 is the same story at 16,368 plots.

## B4. Station cost, and the item that dominates it

Across the 239, on the provisional basis:

| | median | p75 | max |
|---|---:|---:|---:|
| Duty Qadf, m³/d | 131 | 377 | 42,754 |
| Lift, m | 11.4 | 13.1 | 55.5 |
| Hydraulic power, kW | 0.6 | 1.6 | 90.2 |
| Capital (Cabral), OMR | 24,248 | 40,368 | 347,291 |
| Energy, kWh/yr | 2,458 | 7,139 | 722,335 |
| **Energy cost, OMR/yr** | **49** | 143 | 14,447 |
| Total OPEX, OMR/yr | 12,267 | 12,508 | 29,572 |
| **Life-cycle PV, OMR** | **197,144** | 216,647 | 764,082 |
| Life-cycle PV, manning removed | 28,017 | 47,520 | 594,954 |

**Pumping energy is 0.4 % of a station's operating cost.** The 25-year present value of
NWS's manning rule is **169,127 OMR per station — 86 % of the median station's whole
life-cycle cost.** Twenty-one to thirty lifting stations on this network are an
**establishment decision, not an energy decision**, and the report should say so rather than
present a pumping-energy argument that is two orders of magnitude too small to matter.

That single assumption also moves the answer:

| | breaches where digging wins |
|---|---:|
| NWS manning rule applied (12,000 OMR/yr/station) | **10 of 13** |
| Unmanned, visited stations (no fixed establishment) | **2 of 13** |

## B5. Sensitivity — stations kept out of 239

Rows are the marginal excavation rate at 4 m, OMR/m/m; columns are the depth exponent *b*
and whether manning applies. Full grid in `W10/run/research_breakeven_sensitivity.csv`.

| k @4 m | b=1.0 staffed | b=1.5 staffed | b=2.0 staffed | b=1.5 unstaffed |
|---:|---:|---:|---:|---:|
| 10 | 226 | 228 | 228 | 234 |
| 15 | 229 | 229 | 229 | 235 |
| 20 | 229 | 229 | 229 | 236 |
| **30** | **229** | **229** | **230** | 237 |
| 45 | 231 | 231 | 233 | 238 |
| 60 | 232 | 233 | 233 | 238 |
| 90 | 234 | 235 | 236 | 239 |

Across the **entire** plausible range of both the rate and the exponent, the answer moves
between **226 and 239 stations kept out of 239** — that is, between 13 and 0 breaches
droppable. The depth exponent, which the literature argues about, changes the answer by at
most two breaches. **The exponent does not matter. The manning rule does.**

## B6. And at the level the design actually works at, nothing changes

239 breaches are not 239 stations. Project rule 9 consolidates anything within 1.5 km:
**239 breaches → 30 clusters.** For a cluster to lose its station, *every* breach in it must
be eliminable.

> **Clusters where every breach is eliminable: 0 of 30.**
> **Stations kept: 30 of 30, with or without the manning rule, at every rate tested.**

Cluster 1 alone contains 94 breaches. The thirteen eliminable breaches fall in clusters 1, 3, 7 and 10
and the ten droppable ones in clusters 1 (94 breaches), 3 (45) and 10 (2) - every one of
which keeps a station for other members.

**So the honest headline is two-sided.** A look-ahead rule saves ~1.5 MOMR of present value
and removes two very large stations from the *design*, and it removes **no stations from the
count**. Anyone quoting a station count should not expect it to move; anyone costing the
scheme should expect it to.

---

# PART C — the rule

## C1. The decision rule, implementable

For each node *b* where the solved depth passes the cover limit:

1. **Look ahead.** Walk the flow tree downstream from *b* with the station deleted, using
   `invert_noPS[m] = min(invert_shipped[m], invert_noPS[prev] − s·L)`. Stop at the first of:
   - **rejoin** — `|invert_noPS[m] − invert_shipped[m]| ≤ 5 mm`; the station is eliminable;
   - **re-breach** — `depth_noPS[m] > d_max`; the station is deferrable to *m*, not saved;
   - the outlet, or a walk cap of 8 km.
2. **Integrate the excursion.** `DM = ∫ (depth_noPS − depth_withPS) dL` [m²], trapezoid on
   the reach end depths.
3. **Price the dig.** `C_dig = Σ_reach [ f(d_noPS) − f(d_PS) + k_mh·Δd / s_mh ] · L`, with
   `f(d) = (k_ref / (b·d_ref^(b−1))) · d^b`. The anchoring is deliberate: *k_ref* is the
   marginal cost of depth at *d_ref*, the deepest depth for which real rate tables exist,
   so every exponent is calibrated where the data is and only extrapolated beyond it.
4. **Price the station.** `C_PS = C_cap(P) + PVAF · (c_e·E + p_M&E·M&E share·C_cap + staff)`
   with `C_cap = e^4.3184 · P^0.5329 · (k€ → OMR)`, `P = 9.81·Q_peak(m³/s)·H` kW,
   `E = 2.725×10⁻³·Q_adf·365·H/η` kWh/yr, `PVAF = 14.0939` at 5 % over 25 years.
5. **Decide.** Station **only** if `C_PS < C_dig` **and** the excursion rejoins. If it
   re-breaches, keep the station — but record the deferral distance, because the station's
   best position is a network decision, not this node's.
6. **Report `K_FLIP = k_ref · C_PS / C_dig`** with every breach. If it is outside 15–60 the
   decision is settled and no cost data will change it; if it is inside, flag it for the
   priced BoQ.
7. **Consolidate before counting.** Apply rule 9 at 1.5 km and re-test at cluster level. A
   cluster loses its station only if every member is eliminable.

## C2. Inputs, defaults until the BoQs arrive, and what each one is worth

| Input | Default | Basis | Move it and the answer… |
|---|---|---|---|
| `k_ref` marginal excavation cost at 4 m | **30 OMR/m/m** | Central Coast 2019/20 median marginal (93 AUD/m/m ×0.265 ×1.25 escalation); EPA >15 ft implies ~36; Maurer DN200 implies ~57 | **weak**: 10→90 moves the count by 8 of 239 |
| `d_ref` calibration depth | **4.0 m** | the deepest depth with published rate tables | weak, but it is where honesty lives |
| `b` depth exponent | **1.5** | Mansouri & Khanjani; 1.0 and 2.0 as the published bounds | **very weak**: ≤ 2 breaches across 1.0–2.0 |
| `k_mh` chamber cost per m depth / spacing | 300 OMR/m / 50 m | order of magnitude only | weak; it is 6 OMR/m/m, 20 % of `k_ref` |
| Station capital | `e^4.3184·P^0.5329` k€ ×0.42 OMR/€ | Cabral et al., 360 stations | moderate; ±50 % moves 3–4 breaches |
| Energy tariff | 0.020 OMR/kWh | NWS PIAD range 0.01–0.03 | **negligible**: energy is 0.4 % of OPEX |
| Pump efficiency η | 0.65 | wire-to-water | negligible, same reason |
| **Station manning** | **12,000 OMR/yr** | NWS PIAD rule, 1,000 OMR/month per station | **decisive**: 10 → 2 breaches droppable |
| M&E O&M + insurance | 2.0 %/yr of 45 % of capital | NWS PIAD rules | weak |
| Discount rate / period | 5 % / 25 yr, PVAF 14.0939 | G201-p95–96; PROJECT-STATE §2 1f | moderate; at 8 % PVAF is 10.67, i.e. manning PV falls 24 % |
| `d_max` cover limit | 12.00 m to invert | G203-p33, as coded | see §C3 |

## C3. What this says about the 12 m line itself

The 12 m limit is not the problem. `W10/run/p3_cover_rule.csv` already measured the
alternatives — 12 m to invert gives 219 breaches / 21 stations, 12 m *cover* gives 204 / 24,
10 m cover gives 275 / 16, 14 m cover gives 144 / 23 — and the station count barely moves
because consolidation absorbs it. What the rule gets wrong is not the number but the
**greediness**: it fires at the first node over the line and never asks what is 200 m
downstream. That is worth 1.5 MOMR and two very large stations, and it is worth nothing at
all in station count.

**The right fix is not a better threshold.** It is to put station placement inside the design
search, as Duque et al. (2024) do — a vertical arc in the shortest-path graph at every
manhole, so the optimiser decides where a station goes rather than a rule tripping. Their
own conclusion is the one to carry: put the station **upstream, where the flow is small**,
because station cost tracks power at r = 0.99 and head at only 0.72. W10 places stations at
the first *depth* failure, which is uncorrelated with flow — and node 2933 is what that
produces.

---

## Caveats

- **No Omani cost data exists in this project for gravity sewers.** The PIAD rate set is
  water supply, by diameter only, with no depth band. Every absolute OMR figure here is
  provisional and is labelled as such; `K_FLIP` is the column to carry forward because it
  does not depend on them.
- **Every depth law is extrapolated 2–3× beyond its data.** No published rate table reaches
  past ~5 m. The 6 m step where standard trench boxes stop and engineered support begins is
  not represented in any of the three functional forms.
- **The look-ahead is greedy and per-breach.** It answers "should there be a station *here*",
  not "where should the stations be". The 226 deferrable cases contain a real network-level
  optimisation this does not attempt.
- **The station model assumes lift-and-reset in place** — no rising main, no site
  acquisition, no odour control. Central Coast's DSP adds AUD 100,000 per greenfield station
  for odour alone. All three would raise `C_PS` and so favour digging.
- **`p3_lookahead.csv` could not be re-derived.** The script that produced it is not in the
  repository and its node numbering does not match the design graph. The identity claimed in
  §B2 rests on a nearest-depth join, which matched 159 of 226 exactly and had a median
  difference of 0.0 m in that class.
- **Load basis is the placeholder allocation**, as everywhere else in W10. Flows will move,
  and station capital and energy move with them — but both are minor terms.

## Verification, mechanical

- 239 of 239 breaches rebuilt; lift heights agree with `W10_lift_sized.shp` to **0.005 m**.
- The counterfactual recursion is exact by the monotonicity of `min`, argued in §B1 and in
  the script docstring.
- Cross-check on the station capital function: at P = 10 kW it gives 256 k€, and the
  source paper's own cluster scatter (Fig. 3, total cost against total hydraulic power)
  runs to ~2,500 k€ at ~400 kW — 1,705 k€ at 350 kW from the formula. Consistent.
- The G203-p33 quotation was read from the extracted text of
  `Data/PAM-GUD-203 - Wastewater Design Guidelines v1.0.pdf`, not recalled.

## Outputs

| Path | Content |
|---|---|
| `W10/py/research/r10_depth_vs_pumping.py` | re-runnable, ~20 s, modifies nothing upstream |
| `W10/run/research_breakeven_breaches.csv` | 239 rows: excursion geometry, dig cost under three depth laws, station life-cycle cost, `K_FLIP`, cluster id |
| `W10/run/research_breakeven_clusters.csv` | the 30 rule-9 clusters and the verdict per cluster |
| `W10/run/research_breakeven_sensitivity.csv` | 42-cell grid: rate × exponent × manning |
| `W10/run/research_breakeven_curve.csv` | break-even DM and excursion length against station life-cycle cost |
| `W10/run/research_breakeven_lookahead_check.csv` | the join against `p3_lookahead.csv` behind §B2 |
