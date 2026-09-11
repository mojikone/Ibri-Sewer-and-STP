# W13 tmp3 design logic

The logic of `W13/tmp3`. It starts from the logic of the network the engineer accepted on
2026-09-09 (`W13/tmp2/docs/W13_TMP2_DESIGN_LOGIC.md`, frozen with tmp2) and carries the
engineer's rulings of 2026-09-11: the plots' own flows, the gradient grid, the self-cleansing
audit and the guideline's tier names (rules 7 and 10, and the names in rules 5 and 6). Written so it can be followed: one rule per item, in the engineer's words, the number
that defines a rule next to it. No history inside a rule. When a rule changes, the rule is
rewritten and one dated line at its head says what moved. Run results live in the run folder's
`README.md` and `run/stage_a.json`, never here. Nothing is added to this logic without the
engineer's agreement first.

## The idea, in the engineer's words

- **The target is the outfall and the main pipe.** The STP inlet, and the joins on the main
  pipe. Every subnetwork converges on one of them.
- **Gravity is the way the streams go.** It guides where the real ground goes, so the network
  converges on the target the way the water would.
- **Constructable means pipes in straight roads, with the smaller streets hung on them,**
  following the general direction of the terrain while knowing the target. Avoid bends as
  much as possible in the sub mains, and as far as possible in the laterals. Not a strict
  rule; it matters on flat ground.
- **Sub mains first. Then hang the laterals on them, constructably.**
- **No optimization.** No reroute, no trunk built for a pocket, no cost deciding an outlet.
- **Tier names are the guideline's** (engineer, 2026-09-11; G203 p17, p21): the trunk is
  **primary**, a sub main is a **secondary header**, a street pipe is a **secondary main
  sewer**. "Lateral" is the tertiary pipe. The engineer's words above are kept as he said them.
- **Constructability first does not mean go deep. 12 m is the maximum.** Whatever cannot reach
  a target within 12 m remains a pocket. A reroute is possible only if constructability is kept.

## The rules

1. **Read the ground along the streets.** The streets are the draftsman's DXF as drawn
   (`Hydraulic/DWG/road network 03092026 eyeballed.dxf`): dual carriageways already left out,
   the crossings the draftsman drew the only ones, line ends within **3 m** snapped. The
   terrain is the 0.5 m blend read at **2 m**. The fall is taken junction to junction; a run
   is split at an interior high or low more than **0.5 m** above or below both its ends, never
   leaving a piece under **30 m**; a fall under **0.1 m** is noise, not a direction.

2. **The targets.**
   - **Joins on the main pipe.** A junction within **30 m** of the drawn main pipe is a join
     candidate. Only headers join; a street that touches the main pipe does not. Joins are
     kept biggest first, and a candidate within **150 m** of a kept one drains into its
     neighbour, unless its streets then have no path to any target, in which case it gets its
     join back.
   - **The STP.** A junction within **250 m** of the works drains to it. NAMA's built trunk
     within **1.5 km** of the works is in the street set as a right-of-way, the last kilometre
     into the works the engineer allowed.
   - **A direct link.** A basin or island low point links straight to a target when its ground
     falls to it at **0.2 %** over the straight distance, the line is under **4 km** and
     crosses no built or planned plot. To the main pipe a link is at most **150 m** with no
     street between; where a street lies between, the water goes by the streets. The main
     pipe is taken **3 m** below ground until it is laid.
   - **The road out of a settlement.** The roads outside the settlements are the way to the
     works; NAMA's line is not a route. A settlement is every street within **60 m** of a 2006
     sewer. A junction within **150 m** of such a road, whose ground falls to the works inlet
     at **0.125 %** along the roads within **6.5 km**, is an entry. One entry per settlement,
     the lowest. The settlement reaches its entry by its own streets.
   - **The works inlet is 323.0 m**, the as-built manhole 5A-1-FL-STP. It does not change.

3. **Outlets by the flood.** Fill the hollows of the street graph from the targets. A dip
   needing **2 m** of fill or less is crossed unremarked. A deeper basin is not an outlet: it
   drains over its lowest rim into the neighbouring subnetwork, and the extra depth the pipe
   carries to leave it is marked at the basin. A basin needing more than **10 m** of fill is a
   pocket (rule 4). Each junction drains to the outlet the flood reaches it from; no cost
   decides it. A part of the graph with no street path to any target is an island: its lowest
   node is a LOW outlet, reported.

4. **A pocket is taken out of the network.** The pocket is the lake: the junctions of the
   basin below the level the water would need to leave it. What is cut off behind the lake
   drains into it, to the same pump. A pocket floods nothing and pulls no neighbour in. No
   trunk is built for it; it remains a pump candidate, reported with its plots.

5. **Secondary headers are the long straight streets.** 2026-09-11: the guideline's name for
   the sub main; the engine's role is still `sub main`. A street is a chain of runs continuing
   through junctions within **25°** of deflection. A chain is cut where the ground forces it:
   at a crest (rule 1), at a sag more than **0.5 m** below both sides where the water leaves
   the street, and between two junctions that drain to different outlets. From each outlet,
   the longest chain whose lower end touches the outlet or a header already chosen is
   taken, cut at the first chosen junction it meets, and so on until nothing attaches. A
   street shorter than **250 m** is not a header; of a longer street, a piece of at least a
   fifth of that attaches. A chain whose foot does not touch may attach through a connector
   of at most **250 m** along the fall, and the connector becomes header with it. A chain
   points toward the outlet; a chain of level runs is pointed by the outlet's distance. A header
   stays on its own outlet's ground: the boundary run into the next catchment is a
   branch, never part of the stem.

6. **Hang the secondary main sewers.** 2026-09-11: the guideline's name for the laterals;
   the engine's roles are still `lateral` and `branch`. One outlet per junction, no loops. The
   run that leaves a junction is the header's own run, or else the cheapest route to the
   nearest header: length plus **500 m** per metre of trench a pipe at **0.5 %** is forced
   to, a header run at **half** that cost, searched from the outlets, inside the junction's
   own catchment. A leftover street (a branch) drains to its lower end, or to the end nearer
   a header where the ends are level.
   Every other street at a junction starts as a head at the first house gate, the first plot
   centroid within **45 m** dropped square onto the street, or **10 m** along where no plot
   faces it; a street under **15 m** cannot carry a head and is reported. The catchment of a
   pipe is the outlet its tree path ends at.

7. **Lay it heads-down and report the depth.** 2026-09-11 (engineer): sized on the plots'
   own flows, and gradients on a grid above the minimum. Every plot that carries flow in W14's
   `PLOTS_load` loads its nearest pipe within **45 m** with its own **`Q_ULT`** (saturation,
   average dry-weather, m³/d). Summed down the tree, then peaked per pipe: **Merrimack** for
   more than **100** properties, Qpdf = 2.65 Qadf^0.879 in Ml/d (G1-p71); **Peltier** for 100
   or fewer, PF = 1.5 + 1/√Qm, Qm in l/s (G1-p72); properties per plot G_DOM + (POP_year −
   POP) / OR_S. Infiltration **720 l/d per km** by the pipe length upstream, unpeaked
   (G1-p72). The diameter comes from the flow; it is never chosen to flatten the gradient.
   Laid at the **G203 Table 11 minimum** as it is; where the ground forces a steeper pipe, the
   gradient is **rounded up** to steps of **0.05 %**, or **0.025 %** from DN500, so no random
   value is laid. **1.55 m** of cover to invert. Depth is reported at every chamber. Not yet in
   the lay: drops, chamber spacing, the tertiary.

8. **The 12 m rule.** After the lay, in every subnetwork with a chamber past **12 m**, the
   basin behind its deepest chamber (the one with the largest fill on the path into it)
   becomes a pocket (rule 4), one per subnetwork per round, and the rest is laid again. Up to
   **8** rounds; the best round is kept, not the last. No reroute and no trunk: whatever
   cannot reach within 12 m remains a pocket.

9. **The route to the works below 12 m is kept as is** (engineer, 2026-09-09). It is reported,
   not acted on. The overall network, the inlet and the way to the works are checked later,
   when all the subnetworks are prepared.

10. **The self-cleansing audit, on the low case** (engineer, 2026-09-11). The flow is
    **`Q_2030` × 0.61** of the plots upstream, peaked as in rule 7 with the properties counted
    **connected** (2030 × 0.61), and **no infiltration**. Each pipe takes one class:
    **velocity pass**, at least **0.75 m/s** at the low-case peak (G203-p26); else **tractive
    pass**, the laid gradient at least Mara's slope Smin = K·τ^1.23·Q^−0.461 with **τ = 1 Pa**
    and **K = 2.33 × 10⁻⁴**, Q in m³/s, on the true flow with no floor (G203-p27); else **needs
    washing** (G203 §4.2.6, p28). The audit changes no size and no gradient. No regrade class,
    no low-flow threshold. The tractive force sets no gradient at the concept stage.

## Where the engine's reading needed a choice

Flags for the engineer, not rules. Each is one line of configuration or one function.

- **250 m** as the shortest street that is a header: the engine's number, never the
  engineer's.
- **The 12 m rule knows only basins.** A depth that grows on the way to the works, with no
  basin behind it, is not cut. That is the case of the two subnetworks that go to the works.
- **Bends in laterals**: the engine has no rule; the least-depth route decides.
- **A pocket is the lake below its spill level**, and what is cut off behind it drains into it:
  the engine's reading of "whatever cannot reach remains a pocket".
- **A header stays on its own outlet's ground**: the engine's reading, after a pocket's sub
  main had hoisted 40 km of the works' catchment into the pocket.
- **One entry per settlement, the lowest**: the engine's choice among 134 candidates.
- **1.55 m** cover to invert: a Stage A proxy from W13's evidence.
- **A plot's class from `PLOTS_load`** (2026-09-11): derived use Agricultural is agricultural,
  even when metered; a metered plot is built; the rest planned. A plot is served when it
  carries flow. Measured: a 29 ha metered farm south of the works, built in W3's file, is
  agricultural here, so a 120 m link to the main pipe may cross it, and the 59 km around the
  works now leaves by that link instead of the STP.
- **A main-pipe join is not floored** (set aside until the main pipe is sized), so the depth
  at which the 59 km arrives at the main pipe is not checked. In tmp2 it arrived 10.7 m under
  the STP inlet; the shortfall moved, it did not go away.
- **Peltier is not capped** at the guideline's recommended 5.0; below about 8 houses the
  factor passes 5, and those pipes need washing whatever the factor.

## What was kept from W13's logic

| W13 rule | In tmp2 | Why |
|---|---|---|
| 1 ground read along the streets, streams as the guide | kept (rule 1) | |
| 2 outlets by the flood, hollows to 2 m, basin over 10 m a pocket | kept (rule 3) | |
| 2 (late) which outlet a node drains to decided by rule 5's cost | **dropped** | the flood decides: gravity is the way the streams go, no optimization |
| 3 spine to the main pipe, one join per catchment | kept (rule 2) | |
| 3 direct links: 0.2 %, 4 km, no plot; 150 m to the main pipe, no street between | kept (rule 2) | |
| 3 NAMA's corridor as a target | **dropped** | a connection with no design is not a route; the roads outside the settlement are (rule 2) |
| 3 a designed trunk along the streets for a pocket | **dropped** | no optimization; a pocket remains a pocket (rule 4) |
| 3 the test boundary as the scope; converge on the outlet; inlet 323.0; last km on NAMA's alignment | kept (rule 2) | |
| 3 a join floored by the main pipe's own profile | set aside | subnetworks first, their levels at the main pipe later |
| 4 sub mains are the long straight streets, 25°, 250 m, cut at a crest | kept (rule 5) | |
| 4 (late) cut wherever the fall turns | **dropped** | the engineer's ruling of 2026-09-08 |
| 4 cut at a sag the water leaves and at a change of outlet; connector 250 m | kept (rule 5) | without them the west's diagonals attach nothing |
| 4 reach of a bigger pipe on flat ground (2, 4, 5 km) | dropped from the rule | a statement, never used by the engine |
| 5 one outlet per junction, no loops; only sub mains join; heads at gates; catchments follow the tree | kept (rule 6) | |
| 5 least-depth route, 500 m per metre, sub main at half, from the outlets, inside the catchment | kept (rule 6) | |
| 6 a ridge is a boundary | kept as the crest cut (rules 1 and 5) | |
| 7 gradient in three bands | not used | Stage C |
| 8 gradient steps, one gradient per run; diameter never chosen to flatten | steps not used (Stage C); the diameter sentence kept (rule 7) | |
| 9 heads-down lay, sizing at saturation, depth reported | kept (rule 7) | |
| 10 over 12 m reroute first, then cut | **changed** (rule 8) | no reroute; cut only, as the engineer stated the 12 m rule |
| 11 a closed hollow is a real pump | kept (rule 4) | |
| 12 chambers, spacing, bends | not used | Stage C |
| inputs: the DXF trusted as drawn, no generated crossings, islands reported | kept (rule 1) | |
| scope: the built envelope | **changed** | the engineer's test boundary, 21.4 km²; the envelope only defines a settlement |
| outputs: one layer per class, colour by subnetwork, arrows, depth bands, red past 12 m | kept | |

## Inputs

Streets `Hydraulic/DWG/road network 03092026 eyeballed.dxf`; terrain
`Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt`; main pipe `SHP/Main Pipe/Main Pipe.shp` as
redrawn on 2026-09-08; the works at (444387, 2563352), inlet 323.0 m; the scope
`SHP/temp/W13 test boundary.shp`; the 2006 network (`W7/shp/EXISTING_SEWERLINE.shp`,
`OP_STATUE = 1`) only to define the settlements and as the comparison; plots
`W14/shp/PLOTS_load.shp` for everything plot-related: heads, served plots, the
no-plot-in-the-way test, and each plot's own flow (`Q_ULT`, `Q_2030`). Settings in
`py/config_built.py`, blocks "W13 temp 2" and "W13 temp 3".

## Outputs

`dxf/W13_A_tree.dxf`: one layer per class, pipes coloured by subnetwork, thickness by
diameter, an arrow on every pipe, chambers in fixed depth bands (0–2, 2–4, 4–6, 6–8, 8–10,
10–12 m, red past 12 m), a stats text at each outlet, the ground behind. `shp/` the same as
shapefiles, `img/` the overview and the two settlements, `run/stage_a.json` the numbers.
The pipe shapefile carries `TIER` (guideline name), `ROLE` (the engine's), `SLOPE_PCT`, the
flows and the audit (`Q_LOW_LS`, `V_LOW`, `S_MARA_PC`, `CLEANSE`); `run/cleansing_table.md`
and `run/washing_list.csv` the audit's table and list; `run/gate_vs_tmp2.json` the layout
against tmp2. In QGIS, group `Claude W13 temp 3` with the self-cleansing layer and
`tmp3 pipes by depth`.
