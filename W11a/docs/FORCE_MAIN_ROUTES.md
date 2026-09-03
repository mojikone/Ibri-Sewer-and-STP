# FORCE MAIN ROUTES — where W11a pumps, where it does not, and why

**Status: internal working paper, 2026-09-02. Every number is measured from a named
artefact and reproducible with `python W11a/report/forcemains.py`. Nothing here is an
estimate unless it says so.**

*Written while stages 6–9 were being re-run by other agents. §1–§14 are measured against the
stage 3 trunk (`W11a_trunk.gpkg`, written 13:15), which was stable throughout. **§1a is a
snapshot of `W11a.gpkg` at 14:55:17 and will go stale**; it is flagged as such on its face.*

---

## 1. The finding the brief did not expect

**W11a has no main force line to the works, because it does not pump to the works.** The
published trunk delivers **74,675 m³/d and 1,369.8 L/s** to the outfall at
E444,423.0 N2,563,343.0 **by gravity**, arriving at invert **319.940 m aOD**, 8.78 m below a
ground level of 328.724 m. The brief asked for the best route "between the pumping stations
the design needs and the works". Measured against the published layers, that route does not
exist: the only pumped links in the design are three short in-line lifts on the trunk itself,
100 m to 421 m long, each discharging back into the trunk.

The 2006 asset does the opposite. NAMA's built rising main runs **9,993.5 m** from the
existing station at E449,894.95 N2,567,302.32 to the works — and over that corridor the
ground **falls 22.37 m**. It pumps downhill for ten kilometres.

So the question this study can actually answer is not *what route*, it is *what mode*, and
the corridor has already settled the route. On the like-for-like pair the two alignments are
**112 m apart** (§5).

| What the design has | Where | Q peak | Rising main |
|---|---|---|---|
| Lifting station N0000215 (FM-1) | 445,113.2 / 2,567,695.0 | 139.2 L/s | 420.7 m, discharges into the trunk |
| Lifting station N0000281 (FM-2) | 447,697.6 / 2,567,164.5 | 219.0 L/s | 100.0 m, discharges into the trunk |
| Lifting station N0000356 (FM-3) | 464,359.2 / 2,566,792.1 | 29.9 L/s | 300.0 m, discharges into the trunk |
| Outfall to the works | 444,423.0 / 2,563,343.0 | 1,369.8 L/s | **none — gravity** |

*Source: `W11a/shp/W11a_trunk.gpkg` layers `nodes` and `reaches`, `W11a/shp/W11a_trunk_pumped.shp`,
`W11a/run/s3_trunk_stations.csv`, all written 2026-09-02 13:15.*

Two caveats on that table, both material:

- **Stage 7 ran while this study was being written, and §1a below is the result.** The
  underlying demand is `W11a/run/s6_station_demand.csv`: **178** cap-breach station demands on
  the gravity network, unconsolidated, the largest at 109.2 L/s and the median at 3.7 L/s, mean
  lift 10.28 m. Every one of them will need a short rising main back to a gravity point. None of
  them is a main force line to the works — the largest is a district collector.
- **Bat needs no force main on this alignment.** The four BAT sets carry 2,235.7 properties and
  1,752.7 m³/d (`W11a/run/s1_servicing.csv`, S165 / S184 / S181 / S182), all with
  `SYSTEM = central` and `ALT_SYS = satellite`. The nearest trunk node to each of the four sits
  in the **outfall** component — 26 m from S184, 846–1,128 m from the rest — so on the client's
  drawn alignment Bat drains to the works by gravity. *That is a statement about the trunk, not
  about Bat's local network: stage 5b still leaves 30.1 % of plots project-wide unassigned.* If
  the appraisal picks the satellite works instead, the conveyance option disappears with it.
  Either way there is no long rising main from Bat.

---

## 1a. Stage 7 published 98 pumping stations and zero rising mains

**Read at 2026-09-02 14:55:17 from `W11a/shp/W11a.gpkg`, while stages 6–9 were being re-run
by other agents. It is a snapshot of a moving file, and it is reported as one.** Nothing in
this section is mine to fix — `s7_stations.py`, `s8_packages.py` and `s9_export.py` belong to
other agents today.

| Layer | Rows | What it says |
|---|---|---|
| `stations` | **98** | every row `Q_DUTY_LS = 0`, `N_PROP = 0`, `Q_ADF_M3D = 0`, `WELL_M3 = 0`, `RM_EDGE` blank, `COMM_PT = 0`, `WHY = cap`, `STAGE = s8_packages` |
| `rising_mains` | **0** | the schema is right and the layer is empty |
| `nodes` | 49,624 | of which **226** carry `NODE_KIND = station` and **247** carry `outfall` |
| `reaches` | 49,377 / 1,731.7 km | full hydraulics — DN, inverts, cover, velocity, provenance |

Five things follow, and the first three are blocking:

1. **A station with zero duty flow is not a station.** `ST_TYPE = Type 1` on all 98 is a
   consequence of `Q_DUTY_LS = 0` falling in the ≤ 100 L/s band (G203-p40), and `LAND_M2 = 100`
   on all 98 is a consequence of that type (G203-p43 Table 21). Two derived fields inherit a
   zero. Nothing about these stations can be sized, costed or checked until the duty is real.
2. **98 stations and no rising mains means 98 places where the flow stops.** `RM_EDGE` is blank
   on every row, so no station has a published discharge route, and the philosophy's H15 —
   every component ends at exactly one outfall — cannot be satisfied through them.
3. **Three published layers disagree about how many stations exist**: `stations` says 98, the
   `nodes` layer's `NODE_KIND` says **226**, and stage 3's trunk carried **3** more that appear
   in neither. `nodes` also carries **247** outfalls. That is the same class of defect as the
   dual-carriageway count in §7 — two numbers for one thing.
4. **The three trunk lifting stations of §6 are absent from the `stations` layer.** N0000215,
   N0000281 and N0000356 — the only stations in the design with a real duty, a real lift and a
   drawn rising main — are not in the register. The §6 table is currently the only place they
   are designed.
5. **`FLOOD_LV` is honest and should stay that way.** It is populated on all 98, and
   `s7_stations.py` declares it as pending item **ST-1**: *no 1:50 water-surface model exists in
   the project data*, so the level is read off the T50 hazard grid — the highest ground among
   flooding cells within a widening 100 → 300 → 1,000 m radius, or the lowest ground within
   1 km where no flooding cell is found. That is a declared proxy, correctly labelled, and it is
   the right way to handle the gap. What it means in practice: **only 23 of the 98 stations have
   any 50-year hazard answer at their own coordinates at all**, so 75 of the published flood
   levels rest on the "lowest ground within 1 km" branch. The G203-p38 §7.2 freeboard is
   therefore demonstrated, at 77 % of the stations, against a proxy rather than a flood level.
   *(A separate `FLOOD_LV = ground − 1.0 m` appears at `s9_export.py:2036`; that block writes
   `STAGE = "s0_demo"` and is a self-test fixture, not the production path. It did not produce
   these rows — no station's freeboard is 1.000 m.)*

And one number that will not stand still: `W11a/run/audit_W11a.csv`, written 14:35, reports
**2 PASS, 5 FAIL and 15 NOT_CHECKABLE** — 15 of them because the pipe layer it read had no DN
and no inverts. The pipe layer at 14:55 has both. The audit is behind the design, so neither
that CSV nor the commit message claiming "22 of 22 checks pass" describes what is on disk.
**Re-run the auditor against the 14:55 layers before anything here is quoted.**

---

## 2. The rule that governs every force main here, and it is a length rule

G203-p50 §8.2.1 asks for a retention period **"no longer than half an hour"**. G203-p50 §8.1
fixes velocity between **0.75 m/s** (at design minimum flow) and **2.5 m/s** (worst case).
Length = velocity × time, so those two clauses together are a ceiling on **length**, and the
diameter never enters it:

| Velocity in the main | Longest main that still holds 30 minutes |
|---|---|
| 0.75 m/s (the self-cleansing floor) | **1,350 m** |
| 1.0 m/s | 1,800 m |
| 1.5 m/s | 2,700 m |
| 2.0 m/s | 3,600 m |
| 2.5 m/s (the absolute cap) | **4,500 m** |

**Above 4.5 km no force main on this project can meet the guideline's own retention ideal at
any diameter, and at a normal design velocity the real ceiling is 1.8–2.7 km.** The guideline
knows: it says the ideal "is very rarely achieved". But it means the half-hour is a screening
rule for *route length*, not a check to be run after the pipe is sized.

Applied here:

| Main | Length | Retention, one duty pump → all duty | Verdict |
|---|---|---|---|
| FM-1, DN300 | 420.7 m | 7.1 → 3.6 min | inside |
| FM-2, DN400 | 100.0 m | 1.9 → 1.0 min | inside |
| FM-3, DN200 | 300.0 m | 5.3 min (single pump) | inside |
| **Built 2006 main** | **9,993.5 m** | **222 → 67 min** (1.11–3.70 h) | **2.2× to 7.4× over, at every diameter** |

The built main's diameter is not recorded — `OUT_DIAMET = 0` on that row — so its retention is
bracketed by the guideline's own velocity window rather than computed. The bracket is enough:
no diameter rescues it. That is precisely the septicity combination the design philosophy §6
names, and G203-p47 §7.7 tells us what to design for when it happens — **H₂S 50–100 ppm
average, ≤ 200 ppm peak at the termination of a pressure main** where no field data exists.

**See `W11a/report/img/FM04_retention_ceiling.png`.**

---

## 3. What decides whether Ibri pumps at all: the works inlet level

The gravity trunk works only if the works will take it low enough. That number is now fixed
and it is tight.

Holding **1.30 m of cover to crown** (G203-p33 §4.6.3) at every node on the last 9.13 km, and
the **Table 11 minimum gradient of 0.075 %** for DN1700 (G203-p29) below each of them, the
**highest invert the trunk could possibly arrive at the works with is 321.209 m aOD**. The
design lays 319.940 m. **Head-room: 1.269 m.** The binding node is at chainage 7,687 m of the
9,128 m leg.

| | |
|---|---|
| works ground level | 328.724 m aOD |
| trunk arrival invert as designed | 319.940 m aOD (cover 6.985 m, depth to invert 8.785 m) |
| **highest legal arrival invert** | **321.209 m aOD** (cover 5.715 m) |
| head-room | 1.269 m |
| flow arriving | 74,675 m³/d, 1,369.8 L/s |

**Any works inlet set above 321.21 m aOD forces a terminal pumping station at the works.** That
is the one main force line this project might genuinely need, and it is a level decision, not a
routing decision. The existing plant is 1,800 m³/d and will be replaced; the new works' inlet
level is therefore a design choice we can still influence — and the cheapest thing this study
can recommend is to fix it below 320 m aOD before the plant's hydraulic profile is drawn.

**See `W11a/report/img/FM02_works_inlet_long_section.png`.**

### The works leg as designed

| | |
|---|---|
| reaches / length | 59 / 9,127.9 m |
| diameter | DN1700 throughout |
| invert fall / mean gradient | 24.374 m / 0.267 % |
| ground fall over the same leg | 23.608 m |
| cover, min / mean / max | 1.30 / 3.06 / 7.34 m |
| velocity at peak, min / max | 1.20 / 2.22 m/s (against the 3.0 m/s gravity cap, G203-p27 §4.2.2.2) |
| retention through the leg | 112.6 min |
| contact with a dual carriageway | 24.0 m |
| contact with wadi ground | 22.4 m |

*Ground check: the published `GRD_M` on all 59 upstream nodes matches the 0.5 m VRT sample to
0.0000 m. That proves the trunk used the designated terrain (project rule 6); it is a
consistency check, not an independent validation of the terrain itself.*

---

## 4. If a terminal station is forced, it is a bad pipe, and the guideline says why

Assume the works cannot take 319.94 m and the whole 9.13 km leg is pumped instead. The peak
1,369.8 L/s puts it in **Type 3** (design flow above 300 L/s, G203-p40), which carries a
**minimum of 3 duty pumps plus 1 standby** (G203-p40 Table 17). Then:

- the main must pass all three duty pumps at ≤ 2.5 m/s → internal diameter **≥ 835 mm**;
- it must still make 0.75 m/s with one pump running → internal diameter **≤ 880 mm**;
- **no standard diameter falls in that 45 mm window.**

The window itself is a source-derived result worth keeping: with *n* duty pumps the two bounds
are a factor *n* apart, and 2.5 / 0.75 = 3.33, so **a single force main can never carry more
than three duty pumps** under G203-p50 §8.1. Beyond that the guideline's own answer is twin
pipelines with a dedicated hydraulic study (G203-p52 §8.2.3).

And at the only diameter that fits, the hydraulics are poor:

| DN | v, all duty | v, one duty | friction | pump head | shaft power |
|---|---|---|---|---|---|
| 800 | 2.73 m/s ✗ | 0.91 m/s | 72.9 m | 49.3 m | 884 kW |
| **850** | **2.41 m/s ✓** | **0.81 m/s ✓** | **54.3 m** | **30.7 m** | **550 kW** |
| 900 | 2.15 m/s ✓ | 0.72 m/s ✗ | 41.1 m | 17.5 m | 313 kW |
| 1000 | 1.74 m/s ✓ | 0.58 m/s ✗ | 24.6 m | 1.0 m | 18 kW |
| 1100+ | ✓ | ✗ | < fall | **negative** | — |

*Friction by Hazen-Williams, C = 120 for ductile iron at 20 years (G202-p104 Table 21, §7.1.3.2
names Hazen-Williams for smaller diameters and Darcy-Weisbach for larger). Pump efficiency
0.75 wire-to-water is **ours**, screening only. The linear scaling of duty with pump count is
**ours** — parallel pumps on a common main deliver less than n × one pump, so the real window
is wider at the top and this is conservative in the direction that matters.*

Two things fall out of that table:

1. **From DN1100 up the pump head goes negative** — friction no longer eats the 23.6 m the
   ground falls, so the main would drain. G203-p51 §8.2.2: *"Pumping mains shall be designed to
   run full and to remain full at all times."* You cannot solve the friction by using a bigger
   pipe. Throttling it back is not available either: G203-p54 §8.4.4 says throttling valves
   "are not recommended and can only be specified on approval from the Client".
2. **At DN850 the crossover flow is 873.7 L/s and the average flow is 864.3 L/s — 1.01 times.**
   The main would spend its working life sitting exactly on the boundary between draining and
   pumping. That is not a design, it is a control problem.

**This is where the project's own economics note has to be applied with care.**
`W10/docs/research/DEPTH_VS_PUMPING.md` measured manning at **169,127 OMR PV per station,
86 % of the median station's whole-life cost**, against pumping energy at **0.4 % (median
49 OMR/yr)**. That holds for the small lifting stations it was measured on. It does **not**
transfer to a Type 3 terminal station at 550 kW: at the PIAD tariff of 0.020 OMR/kWh and the
PVAF of 14.0939 (5 %, 25 yr, G201-p95–96), a station of this size runs into hundreds of
thousands of OMR of energy present value on its own. **Ranking the three small rising mains on
energy is ranking on noise; ranking the terminal station on energy is not.** Do not carry the
0.4 % figure across the size gap.

**See `W11a/report/img/FM03_diameter_velocity_window.png`.**

---

## 5. Route comparison — the 2006 station to the works

Three alignments, all measured on the 0.5 m terrain, the 50-year hazard grid and the `dual`
column of `SHP/Road centerline 2`.

**A** is the built 2006 rising main as it lies. **B** is the W11a trunk corridor over the same
ground. **C** is the straight line, carried only as a lower bound. B starts at the trunk
junction, **905 m** from the 2006 station, so the raw lengths are not comparable — **A′** is A
trimmed to its own closest approach to B's start (63 m off, at chainage 978 m).

| | A built 2006 | A′ trimmed | **B trunk corridor** | C straight |
|---|---|---|---|---|
| length | 9,993.5 m | 9,015.8 m | **9,127.9 m** | 6,754.0 m |
| ground, start → end | 351.09 → 328.72 | 351.80 → 328.72 | 352.33 → 328.72 | 351.09 → 328.72 |
| net fall | 22.37 m | 23.08 m | **23.61 m** | 22.37 m |
| cumulative rise | 33.66 m | 29.57 m | **25.04 m** | 56.89 m |
| summit above the start | 1.16 m | 0.05 m | **0.02 m** | 0.57 m |
| wadi-class contact | 690 m | 50 m | **30 m** | 480 m |
| — of that, in the first km | **640 m** | 0 m | 10 m | 460 m |
| within 6 m of a dual carriageway | 66.2 m | 66.2 m | **24.0 m** | 0 m |
| closest approach to a dual carriageway | 0 — it crosses | 0 — it crosses | 0 — it crosses | 301.6 m |
| more than 25 m from any road centreline | 30 % | 30 % | 29 % | **84 %** |
| prominent summits → air valves | 14 | 12 | **11** | 21 |
| prominent lows → washouts | 15 | 13 | **12** | 22 |
| access points at 500 m (G203-p50) | 20 | 19 | 19 | 14 |
| isolation valves, 500–800 m (G203-p54) | 13–20 | 12–19 | 12–19 | 9–14 |
| **no hazard-grid answer** | **62 %** | **69 %** | **70 %** | **66 %** |

**Read it this way.** B is **112 m longer** than A′, not shorter — the corridor is effectively
the same street, with a median separation of **10.2 m**, **88.5 %** of A within 200 m of B and **95.0 %**
within 500 m (400 samples at 25 m along A). So
the route is already decided by the ground. What B wins on is quality: **4.5 m less cumulative
rise**, one fewer summit, **a fifth of the wadi contact**, and **24.0 m of dual-carriageway
contact against 66.2 m**.

*All three of A, A′ and B intersect a dual carriageway somewhere — the closest approach is
zero, not a near miss. Project rule 7 permits a **crossing**; what it forbids is running
**along** one. On the works leg the published `ON_DUAL_M` is 24.0 m, matching the exact
geometric measure of B to the centimetre, and it is a crossing. On the trunk as a whole the
auditor still records a genuine along-breach (§7).*

*Road distances here are computed geometrically, not sampled. Sampling them at 10 m made A and
its own trimmed sub-line disagree about the closest approach to a dual carriageway (0.50 m
against 0.17 m) purely because the sample points landed differently — a small thing, but it is
the same class of error as scoring nodata as a pass.*

**C is rejected outright**, not on its length but on legality: 84 % of it is more than 25 m
from any mapped road centreline, so it has no public reserve to sit in (G203-p51 §8.2.2 wants
the right of way; philosophy §4 requires a legal corridor), and it crosses 480 m of wadi-class
ground including a 310 m contiguous run.

**And the whole comparison is scored on ground that mostly has no answer.** The 50-year hazard
grid covers 30–38 % of each alignment; the rest is nodata at −9999.0, which is *finite*, so any
`np.isfinite` guard reports it as dry. The wadi numbers above are the tested fraction only.

**See `W11a/report/img/FM01_force_main_route_options.png`.**

### What the built main tells us — the calibration case

- **9,993.50 m** against a straight-line 6,754.0 m: **sinuosity 1.480**. Installed 2006-01-01,
  project 5A-1. `OUT_DIAMET = 0`, `MATERIAL` null, and NAMA's own remark on the row reads
  *"Data is not reliable and must be used only for reference purpose"*.
- It **pumps downhill**: 22.37 m of net ground fall, and its highest point is only **1.16 m**
  above its own start, at chainage 380 m. The static head is therefore near zero and the whole
  duty is friction — the same trap §4 describes.
- **640 m of its first 840 m is on hazard class 4+ ground.** The 2006 station discharges across
  a wadi. G201-p86 forbids valve chambers and marker posts in the wadi bed or on the
  embankments, and requires isolation and air valves *either side* of an active crossing — so
  the very first valve set on that main has nowhere compliant to sit inside the first
  kilometre. Everything downstream of chainage 4,027 m is clear.
- **It touches a dual carriageway over 66.2 m** (measured as the length inside a 6 m band).
  Project rule 7 permits a short perpendicular crossing and nothing else, so whether that
  66.2 m is legal today depends entirely on whether it crosses or runs along — which the
  as-built record does not say.
- **30 % of it is cross-country** (more than 25 m from any mapped road centreline), maximum
  578 m off-road. That triggers the G203-p51 obligations for a cross-country rising main:
  concrete marker posts at every field boundary and at every practicable change of direction,
  reading "PUMPED SEWER" and the depth to the top of the pipe; non-degradable marker tape
  300 mm above the pipe with a trace wire to a marker post every ~1,000 m.
- **Operationally it is expensive to own**: ~14 air valves, ~15 washouts, 20 access points and
  13–20 isolation valves — of order **50–70 chambers on 10 km**. The three W11a rising mains
  together need **three air valves and three washouts** and no intermediate access point at
  all, because every one of them is shorter than the 500 m access interval.

**Is our proposal consistent with the built main?** Yes on alignment and no on mode. We put
essentially the same line in essentially the same street; we run it as gravity because the
23.6 m of fall is there to be used and scope p12 requires us to use it. The built asset shows
that the corridor is available, buildable and 10 km long — and it shows what pumping it costs
in chambers, retention and septicity.

---

## 6. The three rising mains the design does need

All three are cap-driven — `why = cap` on every row, cover 12.39 / 12.39 / 12.64 m at the
station. All three **rise continuously to the discharge point**, which is exactly the ideal
G203-p50 §8.2.1 asks for and almost never gets, so none of them needs an intermediate air
valve or washout.

| | **FM-1** | **FM-2** | **FM-3** |
|---|---|---|---|
| station node | N0000215 | N0000281 | N0000356 |
| ground / invert at the station | 336.556 / 323.937 | 346.525 / 333.735 | 395.734 / 384.296 |
| properties upstream | 6,932.7 | 11,866.3 | 1,275.1 |
| Q average / Q peak | 5,553.8 m³/d / 139.2 L/s | 9,297.7 m³/d / 219.0 L/s | 963.4 m³/d / 29.9 L/s |
| **station type** (G203-p40) | **Type 2** | **Type 2** | **Type 1** |
| duty + standby (Table 17) | 2 + 1 | 2 + 1 | 1 + 1 |
| wet-well live volume (G203-p48 §7.8, 10 starts/h) | 6.26 m³ | 9.86 m³ | 2.69 m³ |
| length as drawn | 420.7 m | 100.0 m | 300.0 m |
| ground rise along it | +2.01 m | +0.50 m | +2.43 m |
| static lift (stage 3) | 13.03 m | 11.69 m | 12.27 m |
| **admissible diameter window** | 266–344 mm | 334–431 mm | 123–225 mm |
| **proposed DN** | **DN300** | **DN400** | **DN200** |
| velocity, all duty / one duty | 1.970 / 0.985 m/s | 1.743 / 0.872 m/s | 0.952 m/s |
| friction at peak (C = 120) | 5.78 m | 0.78 m | 1.72 m |
| total head at peak | 18.81 m | 12.48 m | 13.99 m |
| shaft power at peak (η = 0.75, ours) | 34.3 kW | 35.8 kW | 5.5 kW |
| retention | 3.6–7.1 min | 1.0–1.9 min | 5.3 min |
| air valves / washouts | 1 / 1 | 1 / 1 | 1 / 1 |
| air valve size (G203-p53 Table 24) | 80 mm | 80–100 mm | 80 mm |
| washout size (G203-p54 §8.4.2) | 100 mm | 100 mm | 100 mm |
| material (G203-p53 §8.3) | DI or HDPE | DI or HDPE | DI or HDPE |
| wadi-class contact | 0 m | 0 m | 10 m |
| closest dual carriageway | 28.3 m | 372.2 m | 12.0 m |
| **no hazard answer along the route** | **12 %** | **90 %** | **73 %** |

**The diameter pick is ours and it is a screening pick**: the largest standard DN inside the
window, because it minimises friction and therefore pump duty, and on mains this short the
retention stays deep inside the half-hour at either end of the window. G203-p50 requires *"A
cost comparison ... to determine which pressure main size will result in the optimum whole life
cost"* before this becomes a selection. Note also that G203-p40 (e) puts the **initial minimum
flow** — not the average — in charge of force-main sizing, with the Table 16 multipliers
(0.25 at 50 L/s average, rising to 0.50 at 5,000). We do not have start-year flows in W11a
yet, so the 0.75 m/s check above is made against one-duty-pump output, which is the right
physical quantity for a wet-well station but is **not** the Table 16 test. That check has to be
re-run when the model years land.

### Route options for each

For FM-2 (100 m) and FM-3 (300 m) there is no alignment choice worth the name: both are within
a few metres of the straight line between the station and the discharge chamber, both stay on
the corridor, and both rise monotonically. The options are recorded for completeness only.

| | Option 1 (recommended) | Option 2 | Why |
|---|---|---|---|
| **FM-1** | as drawn, 420.7 m along the trunk corridor to the chamber at 445,523 / 2,567,654 | extend past FM-2's station to discharge at 447,784 / 2,567,114, ~2.7 km | **Reject option 2.** It does not remove FM-2: the 2.28 km gravity component between the two stations picks up 4,933.7 properties of its own and still needs an outlet. It would add 2.3 km of anaerobic main and take retention from 3.6–7.1 min to **22.8–45.7 min**, past the half-hour ideal at one duty pump, to save nothing. |
| **FM-2** | as drawn, 100.0 m | none credible | The chamber it lifts to is 100 m away and 0.50 m higher. Note stage 3 marks this segment **"GAP CLOSURE - provisional, not the draftsman's line (OPEN S3-1)"** — the alignment is a placeholder and must be confirmed. |
| **FM-3** | **re-sited station**, then ~300 m as drawn | as drawn | **Option 2 is not available.** The station node publishes `IN_WADI = 1` and my independent sample of the 50-year grid at its coordinates returns **hazard class 4**. See §7. |

### Handover — the `rising_mains` rows these three should become

The layer is empty (§1a). Every field in `contract.RISING_MAINS` can be filled from the table
above, and the values below are ready to be written by whoever owns stage 7:

| Field | FM-1 | FM-2 | FM-3 |
|---|---|---|---|
| `US_NODE` / `STATION` | N0000215 | N0000281 | N0000356 |
| `DS_NODE` | chamber at 445,523 / 2,567,654 | chamber at 447,784 / 2,567,114 | chamber at 464,099 / 2,566,941 |
| `DN` | 300 | 400 | 200 |
| `MATERIAL` | DI or HDPE (G203-p53 §8.3) | DI or HDPE | DI or HDPE |
| `LEN_M` | 420.72 | 100.00 | 300.00 |
| `Q_DUTY_LS` | 139.22 | 219.05 | 29.91 |
| `V_DUTY_MS` | 1.970 | 1.743 | 0.952 |
| `V_MIN_MS` | 0.985 | 0.872 | 0.952 |
| `STAT_HD_M` | 13.032 | 11.694 | 12.271 |
| `TOT_HD_M` | 18.814 | 12.478 | 13.992 |
| `RETENT_M` | 3.56 | 0.96 | 5.25 |
| `N_AIRV` / `N_WASH` | 1 / 1 | 1 / 1 | 1 / 1 |
| `SEPTIC_FL` | 1 | 1 | 1 |

`TOT_HD_M` is static lift plus Hazen-Williams friction on the main only, at C = 120 for DI at
20 years (G202-p104 Table 21). It excludes valve, bend and station-pipework losses, so it is a
**lower bound** — the same qualification `s7_stations.py` records as pending item RM-2. The
corresponding `stations` rows need `WELL_M3` 6.26 / 9.86 / 2.69 m³ at `WW_STARTS = 10`,
`ST_TYPE` 2 / 2 / 1, and `LAND_M2` from the G203-p43 Table 21 band for that type — not the
Type 1 band all 98 currently carry.

### The FM-1 / FM-2 cascade

FM-1 and FM-2 are **in series** 2.6 km apart: FM-1 lifts 139.2 L/s over 420.7 m into the head
of a 2.28 km gravity component, which picks up another 4,933.7 properties and 3,743.9 m³/d and
collects to FM-2, which lifts the combined 219.0 L/s over 100 m into the main trunk.
**FM-2's flow and property count already contain FM-1's** — the pair serves 11,866.3
properties and 9,297.7 m³/d in total, not the sum of the two rows. Total lift through the
cascade is **24.7 m** (13.03 + 11.69), and every litre from FM-1's catchment is pumped twice.
Project rule 9 allows cascading stations within ~1.5 km; these are 2.6 km apart, so they are
two independent stations and should be costed and commissioned as two.

---

## 7. Wadi crossings — the procedure, and where it is not being met

### On the force mains

Only FM-3 touches wadi-class ground, and only for **10 m** — a crossing, not a run. But
**FM-3's station itself sits in the wadi**, and that is a different and worse problem:

- the design's own `IN_WADI = 1` on node N0000356, corroborated by an independent sample of the
  50-year grid at class 4;
- G203-p30 §4.4.1: *"Locating pipelines and associated chambers in wadis or areas subject to
  washout during heavy storms must be avoided"*, repeated at G203-p33 §4.6.2;
- G203-p38 §7.2: pump pedestal or building floor, transformers, substation and generator
  **above maximum flood level, floors at least 300 mm above the 1:50-year flood level**.

**Recommendation: re-site N0000356 clear of class 4+ ground before stage 7 costs it.** It is a
Type 1 station on 1,275 properties; moving it is cheap now and impossible later.

**FM-2's station has no hazard answer at all** (`WADI_COV = 0`, nodata at its coordinates). We
cannot demonstrate the 300 mm freeboard of G203-p38 §7.2 for it. That is a data gap, not a
pass.

### The G201 §9.3 obligations, in full, for any crossing we design

Read from the source, G201-p85–86:

1. Collect **hydrogeological, hydrological and meteorological data** — wadi bed profiles and
   cross-sections, flood frequency analysis (1-in-20, 1-in-50, 1-in-100 year), grain size
   distribution of the bed material, long-term bed-level change monitoring — from **CAA and
   MoAFWR**, and incorporate it into the design.
2. **Approvals shall be obtained from MoAFWR** and any other relevant agency.
3. Conduct the investigations and surveys: geophysical, geotechnical, topographic,
   georesistivity, EIA, **hydraulic and scour analysis**.
4. **Ductile iron pipes and fittings over the length of the crossing plus 15 m on either side**,
   with mechanical or detachable joints.
5. **Wadi protection to NWS standard drawings PAM-STD-404**, designed to **prevent flotation**
   of the empty pipeline in flood.
6. **Minimum cover 2 m in soft soil** (G201-p86). G203-p52 §8.2.4 gives **1.5 m to crown at a
   wadi crossing** for a force main, against 1.3 m without protection and 0.5 m with protection.
7. **Isolation and air valves either side** of active and major crossings, and **a washout at
   the low point on one side**.
8. **No valve chambers or marker posts in the wadi bed or on the embankments**, and all valves
   and marker posts visible and fully accessible **while the wadi is in flood**.

Note the tension in 7 and 8: the guideline wants valves either side of the crossing and forbids
their chambers on the bed or the embankments. In practice that puts the valve chambers beyond
the embankment toe, and the schedule has to record where that is.

**A correction to `_BRAIN/08_DESIGN_PHILOSOPHY.md` H1a item 3.** The philosophy says the 1.5 m
figure "sits in the FORCE MAIN section" and adopts it for gravity as a project decision. That is
right about the location and slightly unfair to the clause: G203-p52 §8.2.4 opens *"As for
gravitational sewer, the minimum cover should be …"* and then lists 1.3 / 0.5 / 1.5 m. The
clause is asserting that the force-main covers are **the same as the gravity ones** — so 1.5 m
at a wadi crossing has better standing for a gravity sewer than the philosophy currently gives
it. This does not change the rule, only its status: less "our conservative choice", more "the
guideline's own figure, stated in the force-main section". **Recorded for the philosophy's
owner; not edited here.**

### What the published trunk actually does at its 81 wadi crossings

Measured on `W11a/shp/W11a_trunk.gpkg` layer `crossings` (91 rows: 81 wadi, 10 dual):

| Test | Source | Result |
|---|---|---|
| cover below 1.30 m | G203-p33 §4.6.3 / p52 §8.2.4 | **5 of 81**, worst 1.29 m |
| cover below 1.50 m | G203-p52 §8.2.4, wadi crossing | **35 of 81** |
| cover below 2.00 m | G201-p86, soft soil | **55 of 81** |
| within 5° of square | philosophy H1a item 1 | 75 of 81; worst 60.5° |
| **DI over the crossing + 15 m each side** | G201-p86 | **8,253 m = 9.6 % of the 85.55 km trunk** |
| method | — | all 81 `open_cut`; the 10 dual crossings are `thrust_bore` |
| **MoAFWR approval** | G201-p85 | `APPROVED = 0` on all 91 |

**Three defects for the stage owners** (reported, not fixed — `s3_trunk.py`, `s6_levels.py` and
`w11a/contract.py` are not mine):

- **The trunk publishes `MATERIAL` = GRP (549 reaches) and PVC-U (205), and `CONSTR` =
  `open_trench` on every one of the 754.** G201-p86 requires ductile iron over each wadi
  crossing plus 15 m either side — about 8.25 km of the trunk. There is no field on `reaches`
  or on `crossings` that can carry a crossing material, so the requirement is currently
  invisible to the BoQ. It is also inconsistent internally: `CONSTR = open_trench` on the ten
  reaches whose crossings register says `METHOD = thrust_bore`.
- **The crossings register cannot express the G201 §9.3 obligations.** It carries `CROSS_ID`,
  `EDGE_UID`, `OBSTACLE`, `LEN_M`, `ANGLE_DEG`, `METHOD`, `COVER_M`, `APPROVED` and provenance
  — and nothing for the scour analysis, the bed-level monitoring, the anti-flotation check, the
  PAM-STD-404 protection or the valve positions the clause requires. `APPROVED = 0` on every
  row is honest but it is the only trace of the MoAFWR obligation.
- **The dual-carriageway count disagrees with itself.** The published `reaches` layer carries
  `ON_DUAL_M > 0` on **10 reaches totalling 535 m**; the auditor's independent recompute
  (`W11a/run/audit_W11a_trunk.csv`, checks H1 and R3) reports **5 reaches and 0.44 km**. Both
  are FAIL either way, but two numbers for the same constraint means one of them is wrong, and
  under the philosophy's provenance rule that is a blocking finding on its own.

---

## 8. Valves, access and appurtenances — the schedule the guideline requires

For any force main on this project, from G203 §8.4 and §8.2:

| Item | Rule | Source |
|---|---|---|
| Access to the pipe | every **500 m** — removable section in a valve chamber, or an air valve, or a separate access chamber | G203-p50 |
| Air valves | at high points; **double orifice** on transmission mains; approach gradient not flatter than 1:500 and the gradient away not flatter than 1:300; also at significant changes of gradient; number **kept to a minimum**; separate isolation gate valve with bevel gearing so the air valve can be removed without shutting the main | G203-p53 §8.4.1 |
| Air valve size | ≤300 mm bore → 80 mm; 300–500 → 80–100; 600–900 → 150; 1000–1200 → 200; 1300–1600 → 2 × 200 | G203-p53 Table 24 |
| Washouts | at low points, **adjacent to roads for tanker access**; spaced so the section empties in **3–4 hours**; minimum 100 mm | G203-p54 §8.4.2 |
| Washout size | ≤400 mm → 100 mm; 500–800 → 150; 900–1200 → 200; ≥1200 → 300 | G203-p54 §8.4.2 |
| Isolation valves | in-line at about **500 m, not exceeding 800 m**; bypass or gearing above 450 mm; eccentric plug preferred over gate, subject to a life-cycle cost comparison | G203-p54 §8.4.3 |
| Profile | minimum gradient **1:500 rising, 1:300 falling, never below 1:750**, even on flat ground | G203-p50 §8.2.1 |
| Separation | **3.0 m horizontal** to a water main; the force main crosses **under** with **450 mm** vertical clearance; one full length of water pipe centred so both joints are as far from the force main as possible | G203-p51 §8.2.2 |
| Position in a highway | outside of the main in the **vehicle carriageway, not the footpath**, at least **1 m from the kerb line**; manholes at least 0.5 m from the kerb | G203-p51 §8.2.2 |
| Corridor width | for sewage force mains, **dictated by the valve chamber dimensions, case by case** — there is no table | G203-p33 §4.6.2 |
| Termination | into a manhole, **not more than 300 mm above the flow line**; water seal against sulphide release; trapped gases force-vented through odour control; H₂S monitoring at the termination manhole to be studied; heavy-duty protective lining or corrosion-resistant construction; vertical bell-mouth where possible | G203-p55 §8.5 |
| Cross-country marking | concrete marker posts at every field boundary and at every practicable change of direction, reading "PUMPED SEWER" and the depth to pipe top; marker tape 300 mm above the pipe with a trace wire to a post every ~1,000 m | G203-p51 §8.2.2 |

Applied to FM-1/2/3: **one air valve at the discharge summit and one washout at the station low
point on each, no intermediate access point, no in-line isolation valve** — every main is
shorter than the 500 m interval. Sizes as in the §6 table. All three terminate into a trunk
chamber, so all three need the §8.5 water seal, force-vented odour control and lining, and all
three should carry `SEPTIC_FL = 1` when stage 7 writes the `rising_mains` layer.

---

## 9. What needs a client decision

| # | Decision | Why it cannot be made here |
|---|---|---|
| **D1** | **The works inlet invert.** Confirm it will be set at or below **319.94 m aOD**. Above **321.21 m aOD** the trunk cannot reach it by gravity at all and a Type 3 terminal station (3 duty + 1 standby, ~550 kW, 41 m³ wet well) becomes unavoidable. | It is the plant's hydraulic profile, not ours, and the existing 1,800 m³/d works will be replaced. Open item S3-3 in `_BRAIN/00_CURRENT.md`. |
| **D2** | **The fate of the 2006 station and its 10.0 km rising main.** The W11a trunk runs gravity down the same street — median separation 10.2 m, 88.5 % within 200 m. Decommission, retain as standby, or re-purpose? | It is a live NAMA asset serving the built 5A packages, and the answer changes both the construction sequence and the trunk's staging. |
| **D3** | **535 m of trunk on a dual carriageway** (10 reaches, or 5 reaches / 0.44 km on the auditor's recompute) — a defect of the client's drawn Main Pipe alignment, not of our routing. | Project rule 7 admits no pipe along a dual carriageway. Only the client can move their own alignment. |
| **D4** | **MoAFWR approval for 81 trunk wadi crossings** plus whatever the force mains need, with the CAA/MoAFWR data collection G201-p85 requires. `APPROVED = 0` on every row today. | A statutory approval with a lead time; it should start now, not at detailed design. |
| **D5** | **Re-site lifting station N0000356 (FM-3)** off class 4 hazard ground. | Cheap now, impossible after the land is reserved. |
| **D7** | **How many pumping stations the scheme actually has**, once §1a is resolved. Three published layers currently say 98, 226 and (with stage 3's trunk) 3 more. The client's land reservation, manning cost and O&M headcount all follow from that number, and manning is 86 % of a small station's whole-life cost. | It is a design defect first — but the answer is a commitment the client has to make land available for. |
| **D6** | **Whether Bat is conveyed or served by a satellite works** — 2,235.7 properties, 1,752.7 m³/d, `BOTH = 1` in the servicing table. On the current alignment conveyance needs no rising main; a satellite works removes the question entirely. | Philosophy §8a keeps both in the options appraisal deliberately. |

---

## 10. What needs data we do not have

| # | Gap | Effect |
|---|---|---|
| **G1** | **The 50-year hazard grid does not cover the study area.** 62 % of the built main, 70 % of alignment B, 90 % of FM-2's route and 73 % of FM-3's have **no answer**. Its nodata is −9999.0, which is finite. | Every wadi statement above is about the tested fraction. G203-p38 §7.2's 300 mm freeboard cannot be demonstrated for two of the three stations. Full 1:50 coverage is a data request. |
| **G2** | **The existing works inlet invert** (open item S3-3). | D1 cannot be closed without it. |
| **G3** | **The built rising main's diameter, material and condition.** `OUT_DIAMET = 0`, `MATERIAL` null, and the row is marked reference-only by NAMA. | Its retention can only be bracketed (1.11–3.70 h), and D2 cannot be costed. |
| **G4** | **Start-year and 2030 flows.** Stage 5c publishes ultimate flows only. | G203-p40 (e) and Table 16 make the **initial minimum flow** the sizing case for a force main. The 0.75 m/s check in §6 is made on one-duty-pump output instead, which is the right physical quantity but not the Table 16 test. |
| **G5** | **Pipe pressure class — PAM-SPC-207.** | The internal diameters in §4 and §6 are nominal. For the 835–880 mm window a 5 mm wall change moves the answer, so the window cannot be resolved into a real pipe until the class is known. |
| **G6** | **Pump manufacturer curves.** | The linear duty scaling in §4 and §6 is ours. Real parallel-pump duty points come off the system curve, and they widen the window at the top. |
| **G7** | **NWS station establishment cost, and the manning rule at Type 3 scale.** | The 86 % / 0.4 % split in `DEPTH_VS_PUMPING.md` was measured on small stations. §4 shows it does not transfer to a 550 kW terminal station. |
| **G8** | **A surge analysis** for any main adopted. G203-p53 §8.4.1 makes air-valve size, location and number a function of it whenever the valves also mitigate transients. | The air-valve schedule in §8 is a screening schedule only. |
| **G9** | **Soil type along each crossing.** G201-p86's 2 m cover applies "in soft soil"; 55 of 81 trunk crossings are below 2 m. | Whether those 55 are breaches depends on a geotechnical answer we do not have. |

---

## 11. A blocker for any future force-main routing on the corridor graph

The corridor network cannot currently be used to route between the city and the works. Built
from `W11a/shp/W11a.gpkg` layer `corridors` (26,450 edges, 2,234.8 km) on its declared
`US_NODE`/`DS_NODE`:

- **311 components.** The two largest are **810.2 km** and **725.0 km** — together 69 % of the
  network — and **they are not connected to each other**.
- The corridor node nearest the 2006 station is in the 810.2 km component; the node nearest the
  works is in the 725.0 km one. **A shortest path between them does not exist.**

That is why the alignments in §5 are measured on the built main and the published trunk rather
than searched on the corridor graph. It is a defect in stage 2's output, reported here for its
owner; `s2_corridors.py` is not mine to change.

---

## 12. Figures

All four are drawn by `W11a/report/forcemains.py` through `W11a/report/figkit.py`, at 200 dpi,
into `W11a/report/img/`. Every figure carries its own source line and its own untested share.

| File | What it shows |
|---|---|
| `FM01_force_main_route_options.png` | Route map. Alignments A, A′, B and C between the 2006 station and the works, over the offline Esri mosaic at 30 % opacity, with answer-free ground hatched, the three lifting stations, and the full comparison table in the databox. |
| `FM02_works_inlet_long_section.png` | **The hydraulic-grade figure.** Top: the last 9.13 km of trunk as designed — ground, invert, cover band, the 321.21 m arrival ceiling and the band a works inlet may not sit in. Bottom: the same task pumped — the DN850 hydraulic grade against the ground on both alignments. |
| `FM03_diameter_velocity_window.png` | Why pumping this flow is expensive: velocity and pump head against diameter, with the 835–880 mm window G203 admits, the 2.5 m/s cap distinguished from the 3.0 m/s gravity maximum, and the diameters at which the main can no longer be kept full. |
| `FM04_retention_ceiling.png` | The half-hour retention ceiling as a length rule, with FM-1/2/3 inside it and the built 2006 main outside it at every velocity in the window. |

Rebuild: `python W11a/report/forcemains.py` (add `--numbers` to print the measurements without
redrawing).

---

## 13. Citation register — every guideline value used, with its page

| Value | Clause | Page |
|---|---|---|
| Rising main maximum velocity **2.5 m/s** | §8.1, *"The maximum allowable velocity (worst case scenario) in the pipe shall be not greater than 2.5 m/s"* | **G203-p50** |
| Rising main minimum velocity **0.75 m/s** at design minimum flow; **1.0 m/s** for intermittent flow; **1.2 m/s** vertical | §8.1 | **G203-p50** |
| Gravity maximum velocity **3.0 m/s** — *not* the rising-main cap | §4.2.2.2, *"the maximum velocity shall not exceed 3 m/s at the design depth of flow"* | **G203-p27** |
| Force main minimum **75 mm** ID for non-clog pumps, 50 mm for grinder pumps | §8.1 | **G203-p50** |
| Retention **no longer than half an hour**; rise continuously; min gradient **1:500 rising, 1:300 falling, never below 1:750** | §8.2.1 | **G203-p50** |
| Access to the pipe **every 500 m** | §8 preamble | **G203-p50** |
| Whole-life cost comparison decides the diameter | §8 preamble | **G203-p50** |
| Run full and remain full at all times; right of way; **3.0 m** to water mains; cross **under** with **450 mm**; carriageway not footpath, **1 m** from the kerb; straight lines, pre-formed anchored bends; cross-country marker posts and marker tape | §8.2.2 | **G203-p51** |
| Twin pipelines only with a dedicated hydraulic study; same for a punctual obstacle crossing | §8.2.3 | **G203-p52** |
| Cover **1.3 m** without protection, **0.5 m** with, **1.5 m at a wadi crossing** | §8.2.4 | **G203-p52** |
| Pressure main material: **ductile iron and HDPE** | §8.3 | **G203-p53** |
| Air valves at high points, double orifice, 1:500 approach / 1:300 away, number minimised, separate isolating gate valve; **Table 24** sizes | §8.4.1 | **G203-p53** |
| Washouts at low points, tanker access, **3–4 hour** emptying, minimum 100 mm, sizes by main bore | §8.4.2 | **G203-p54** |
| Isolation valves at ~**500 m, not exceeding 800 m**; bypass/gearing above 450 mm | §8.4.3 | **G203-p54** |
| Throttling valves **not recommended**, client approval only | §8.4.4 | **G203-p54** |
| Termination into a manhole **≤ 300 mm above the flow line**; water seal; force-vented odour control; H₂S monitoring; lining; vertical bell-mouth | §8.5 | **G203-p55** |
| Station floors **300 mm above the 1:50-year flood level**; site approved by NWS at concept/preliminary stage | §7.2 | **G203-p38** |
| **Table 16** minimum pump flow factors 0.25 / 0.35 / 0.45 / 0.50 at 50 / 500 / 2,500 / 5,000 L/s average; *"the initial minimum flow rate shall be considered in sizing the force main"* | §7.3 | **G203-p40** |
| Station **Type 1 ≤ 100 L/s, Type 2 ≤ 300, Type 3 > 300**; **Table 17** minimum 1 / 2 / 3 duty pumps + 1 standby | §7.3 | **G203-p40** |
| Station pipework 2.5 m/s at maximum flow, 0.6 m/s at minimum; valves 2.5 m/s | Table 17 | **G203-p41** |
| H₂S design values **50–100 ppm average, ≤ 200 ppm peak** at the termination where no field data | §7.7 | **G203-p47** |
| Wet well **V = 0.25 Q T**, T = 3600 / starts per hour, **minimum 10 starts/h** to 30 kW | §7.8 | **G203-p48** |
| Minimum cover **1.3 m to crown**, 0.5 m with concrete protection, **3 m** horizontal clearance | §4.6.3 | **G203-p33** |
| Force-main corridor width **case by case, set by the valve chambers**; pipelines and chambers in wadis to be avoided | §4.6.2 | **G203-p33** |
| Wadis and flood-prone areas prohibited to **pipelines and associated chambers**; inlet angle ≥ 90°; **Table 12** chamber spacing | §4.4.1, §4.4 | **G203-p30** |
| Full wadi-crossing procedure: CAA/MoAFWR data, **MoAFWR approval**, scour and hydraulic analysis | §9.3 | **G201-p85** |
| **DI over the crossing + 15 m each side**; **PAM-STD-404** protection; anti-flotation; **2 m cover in soft soil**; isolation and air valves either side, washout at the low point; **no valve chambers or marker posts in the bed or on the embankments** | §9.3 | **G201-p86** |
| Head-loss equations: Darcy-Weisbach for larger pipes, **Hazen-Williams for smaller**; **Table 21** C = 140 new / **120 at 20 years** for ductile iron, 150 for HDPE | §7.1.3.2 | **G202-p104** |
| Discount rate and period for present value (5 %, 25 yr, PVAF 14.0939) | — | **G201-p95–96** |
| *"avoid pumping and utilize gravity as much as practically possible"* | scope p12 | **client TOR** |

### Values used here that are OURS, not the guideline's

| Value | What it is | Where it appears |
|---|---|---|
| Hazard classes **(4, 5, 6)** = "wadi ground" | AR&R flood-hazard classes, keyed on danger to people and vehicles, standing in for G203-p30 §4.4.1's *"areas subject to washout"*, which is a **scour** criterion | every wadi number in §5, §6, §7 |
| **25 m** from a road centreline = "cross-country" | a proxy for "outside the public right of way" (G203-p51) | §5 |
| **0.30 m** prominence on a 50 m smoothed profile = a summit | G203-p53 requires air valves at high points and says to keep the number to a minimum, and gives no threshold | summit and washout counts in §5, §6 |
| **η = 0.75** wire-to-water | screening only | all kW figures |
| **Duty scales linearly with the number of running pumps** | screening only; parallel pumps on a common main deliver less | the 835–880 mm window, the velocity checks in §6 |
| **Largest standard DN inside the window** | a screening pick, pending the G203-p50 whole-life cost comparison | the DN300 / DN400 / DN200 in §6 |
| **10 starts/h** for the wet-well volumes | the guideline minimum for motors to 30 kW; the manufacturer sets the real number | §6 |

---

## 14. Artefacts read

| Path | Written | Used for |
|---|---|---|
| `W11a/shp/W11a_trunk.gpkg` [`nodes`, `reaches`, `crossings`] | 2026-09-02 13:15 | the trunk, the works leg, the three stations, the 81 wadi crossings |
| `W11a/shp/W11a_trunk_pumped.shp` | 2026-09-02 13:15 | the three drawn rising-main routes |
| `W11a/run/s3_trunk_stations.csv` | 2026-09-02 13:15 | station flows, lifts, discharge points |
| `W11a/run/s6_station_demand.csv` | 2026-09-02 13:10 | the 178 unconsolidated cap-breach demands |
| `W11a/run/s1_servicing.csv` | 2026-09-02 11:03 | the Bat sets and the satellite/central split |
| `W11a/run/audit_W11a_trunk.csv` | 2026-09-02 14:07 | the independent dual-carriageway and wadi recomputes |
| `W11a/shp/W11a.gpkg` [`corridors`, `corridor_nodes`, `crossings`] | 2026-09-02 13:43 / 14:05 | the corridor connectivity blocker in §11 |
| `W11a/shp/W11a.gpkg` [`stations`, `rising_mains`, `nodes`, `reaches`] | **2026-09-02 14:55:17** | §1a — a snapshot of a file three agents were writing |
| `W11a/run/audit_W11a.csv` | 2026-09-02 14:35 | §1a — 2 PASS, 5 FAIL, 15 NOT_CHECKABLE, already behind the layers |
| `W11a/py/s7_stations.py`, `s9_export.py` | read only | the ST-1 `FLOOD_LV` proxy and the `s0_demo` fixture in §1a |
| `Data/Received/09-RECEIVED/NAMA/IBRI/WW/SHIP/FORCELINE_IBRI.shp` | 2026-08-16 18:19 | the built 2006 rising main (the one `STATUS = Ex` row of nine) |
| `Data/Terrain/Sat_0p5m/IBRI_0p5_VRT2.vrt` | — | every ground profile (project rule 6) |
| `Data/04 Lekhuwair/Hazard_T50y.tif` | — | the 50-year hazard grid, nodata −9999.0 |
| `Hydraulic/SHP/Road centerline 2/Road_Centercline.shp` | — | the `dual` column and the road-proximity proxy |
| `Data/PAM-GUD-203`, `-201`, `-202` | — | every citation in §13, read from the PDF |
