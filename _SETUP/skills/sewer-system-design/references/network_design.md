# Network design: own model, studies, and the design chain

## Contents
1. Make your own model give SewerGEMS's answer
2. The studies behind the decisions
3. The design chain, step by step
4. Checks on a finished design

## 1. Make your own model give SewerGEMS's answer

Reference: `scripts/py/own_design.py`, then `final_design.py`; proof by `compare_own_sewergems.py`.

Read the rules off a SewerGEMS design of the same network (Ibri: SC1-2056, job 074), and check each one on it before use:

- **Flow** at a pipe = PF × the unit loads upstream (its upstream manhole included) + 720 L/day per km on the conduits
  upstream + the transfers from upstream outfalls, which are not peaked again.
  - PF is the model's own Extreme Flow Setup table, linear between rows, on the cumulative base in L/s. At Ibri that is
    "Peltier100-Merriamck" (the model's spelling): Peltier to 1 L/s, Merrimack above, with a step row 1.001 L/s → 3.56.
- **Gradient:** the Table 11 minimum of the pipe's size (p29). Read the gradient per size off SewerGEMS's design (the most
  common gradient of each size in use), and take Table 11 for a size it does not use. All 19,083 Ibri pipes sat on it.
- **Size:** the smallest catalogue size whose Colebrook-White capacity (ks 1.5 mm, ν 1.141e-6) at the d/D limit (0.65 to
  350 mm inside diameter, 0.50 above) carries the flow **at the gradient of the pipe's current size**.
  - Repeat pass after pass from the modeller's sizes until nothing changes. That is SewerGEMS's own procedure.
  - Sizing each candidate at its own gradient instead gave 63 pipes one size smaller (DN315→280, 450→355, 500→450).
- **Catalogue:** every size SewerGEMS offers. Missing DN1200 was the only difference in the blind test.
- **Inverts:** crowns matched and 1.3 m cover over the soffit. Every one of Ibri's 3,612 head pipes sat exactly at that
  cover.
- **Velocity:** Colebrook-White at normal depth on the laid gradient.

**The blind test, the gate for everything after.** Design one case with your own code before SewerGEMS finishes, then
compare. Ibri SC1-2051:
- the same size on 19,056 of 19,083 pipes; the other 27 were DN1200, which was missing from the catalogue;
- with DN1200 added, the same size on all 19,083 pipes in 2051 and in 2056;
- design flows within 0.1 % on every pipe, the largest difference 0.004 %;
- opening-year velocities different by a median of 0.000 m/s (5–95 %: ±0.001).

Until a test like this passes, your model is not a design tool.

## 2. The studies behind the decisions

The engineer makes these decisions. Your job is to put the evidence in front of them as a table and a map.

- **Gradient limit.** Run the chain at 0.50, 0.75 and 1.00 %. For each limit report:
  - stations and lifts, how many are new and how many are joined by gravity;
  - the deepest manhole left;
  - the length above DN200 that self-cleanses at the opening year.
  - Ibri SC1-2056: 82.6 %, 93.9 % and 98.1 % of the pipe above DN200 self-cleansing, and 0.75 % was chosen.
- **Design year.** Design for opening + 25 (Ibri 2056 = 2031 + 25), then the years either side (2051, 2061) to show what
  the choice costs. Check self-cleansing at the opening-year peak, and recheck five years later to see whether the
  leftover pipes self-clean by then.
  - Ibri's first rule was to search: design 2056; if the opening year passes, try 2061, then 2066 and 2071; if it fails,
    step back to 2051. That became the three-year comparison.
- **Station decisions.** Where removing a station needs a deeper outfall, show each candidate: depth, flow, and what it
  saves. Record the engineer's choice in a file the chain reads (Ibri: `fixed_stations.json`), so a re-run keeps it.

## 3. The design chain, step by step

Reference: `scripts/py/final_run_all.py` runs the steps for every case (scenario × design year) in parallel, and repeats
until the lift stations no longer change.

1. **Design** (`final_design.py <SC> <year> --lifts`):
   - flow as in §1, at the design-year loads; pumped transfers from other systems added as their peak;
   - size as in §1, pass after pass until no size changes;
   - export the conduits at the design year and at the two check years (the opening year and five years later).
2. **Split** (`split_deep_subnetworks.py <case> <exports> <split> 0.0075 --fixed=fixed_stations.json`):
   - **Steepen** pipes above DN200 to reach 0.75 m/s at their opening-year peak, up to the gradient limit, with one gradient
     per street run. A street run follows, at each manhole, the arriving pipe of the same size closest to its line.
   - **Re-lay.** A pipe's upstream invert is the lowest of three:
     - the lowest invert arriving at its upstream manhole;
     - the lowest arriving soffit minus its own diameter (crowns matched);
     - the shallowest invert its cover allows (1.3 m over the soffit at both ends).
     The downstream invert is the upstream invert minus gradient × length.
   - **Cut.** Where a subnetwork stays deeper than the depth limit for good, the last manhole within the limit becomes a
     station. Its flow is lifted to the next manhole, which starts again at minimum cover. Leave dips that come back within
     the limit alone, and never move an outfall.
   - **Join by gravity** where an outfall within the depth limit lies within one manhole spacing (Table 12) of the manhole
     it pumps to. Keep a join only if the station count goes down.
   - Repeat until nothing changes; the fewest stations wins.
3. **Fewer stations** (`reduce_stations.py`, settled in `fixed_stations.json`):
   - drop a station, or merge two into one where both flows pass;
   - a change is allowed while every added station and the outfall stay within their cap (Ibri 14.65 m) and no manhole
     passes its cap (Ibri 16.5 m);
   - among the allowed changes, prefer the shallowest outfall, then the shallowest deepest station.
   - The engineer's words (Ibri, 2026-11-18): "we are trying to stick to 12 m depth, but at times a bit deeper can help
     reducing a pump or lift".
4. **Self-cleansing check** (`final_selfcleansing.py`):
   - pipes above DN200 at 0.75 m/s at the opening-year peak;
   - those that miss are checked at the peak five years later;
   - the rest go on the flushing list (G203 §4.2.6: early phases need more frequent inspection and cleansing).
5. **Names** (`final_naming.py`):
   - a station is a **lift** when its force main reaches a manhole within one Table 12 spacing; otherwise it is a **pump**;
   - pumps are P1, P2 ...; lifts are P<n>L<k>;
   - manholes and pipes are <section>-M<k> and <section>-P<k>; a force main is <station>-RM.
   - G203 calls both pumping stations, Type 1/2/3 by flow (p40 Table 17).
6. **Stations sized** (`final_products.py`):
   - duty = the design-year peak, raised so the force main keeps 1.0 m/s (p50);
   - force main = the size from 75 mm with the least power at v ≤ 2.5 m/s;
   - head = static + Hazen-Williams friction (C 120) + 10 % minor losses;
   - wet well 1.5 m below the incoming invert; discharge 0.3 m above the receiving invert, or 3.0 m above the ground at a
     plant;
   - wet-well live volume V = 0.25·Q·T at 10 starts an hour (p48);
   - wire-to-water efficiency 0.65;
   - energy = power × the hours the duty takes to pass the year's average flow.
7. **Quantities and cost:** `final_boq.py`, `final_financial.py` (see `costs_and_te.md`).

## 4. Checks on a finished design

- **No pipe over its d/D limit at the design year,** judged at two decimals.
- **The other design years at the adopted year's peak** (`design_year_check.py`): the pipes of the 2051 and 2061 networks
  that run over their limit at the 2056 peak. A pipe is over when d/D ≥ limit + 0.005.
- **Maximum velocity 3.0 m/s** (p27): count the pipes over; Ibri had none.
- **Depth:** list every manhole past 12 m with its reason (an accepted station decision, or a dip).
- **Drops:** at Ibri, junction drops over 2 m were studied separately and kept as a record. Shafts were left only at trunk
  junctions, DN900–DN1600.
- **SewerGEMS referee**, pipe by pipe (`final_sg_compare.py`). It must show:
  - flows within 0.1 %;
  - no pipe over its limit;
  - the same length under 0.75 m/s at the opening year. Ibri had 4.2 km for the 2051 designs, 9.0 km for 2056 and 14.1 km
    for 2061. The steepened pipes, laid to 0.75 m/s exactly, read 0.749–0.750 m/s in the model.
