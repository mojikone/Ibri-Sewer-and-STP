# W6 - what changed, in plain words

Written 19 August 2026. Every number comes straight from `W6/run/summary.json`.

## The thing you caught

You asked why there were chambers deeper than 12 m when 12 m is the limit. You were right, and
the cause was in my own code. The check that enforces the depth limit had an exemption: any
chamber flagged as belonging to a "pumping pocket" was skipped. The run then decided those
pockets were too small to justify a station and dismissed them - so **71 chambers sat between
12 m and 21.3 m deep with no pump and no warning**, and the audit reported no failure.

That exemption is deleted. The limit is now checked at every chamber and along the trench
between chambers, and nothing can opt out of it.

## What happens instead

When the sewer would pass 12 m, a **pumping station** goes in just before that point. The sewage
is lifted and the pipe restarts about 1.5 m below the surface, so the next stretch runs by
gravity again. That is the normal answer and the one the guideline intends. Pumps are never
removed by digging deeper.

The pipe leaving a pump - the rising main - is sized on the **pump duty**, not on the rate
sewage arrives. A pump fills a wet well and empties it faster than it fills, and that is what
keeps the flow between 0.75 and 3.0 m/s. Sizing it on the arriving flow would have given a pipe
far too slow to keep solids moving.

## The main pipe

It now runs where you asked: along the streets on the **western edge**, then along the
**southern side beside the dual carriageway** - 2.1 km, with 44
points where side networks can join. Median distance from the line you described:
76.7 m. Every street drains to its **nearest** joining
point instead of travelling across the area to a single outfall, which is what used to bury the
pipe.

## How many pumps, and why any at all

The route is searched several times over. Each attempt makes the streets that forced deep
digging last time expensive, so the design gets a chance to find a way round instead of a pump.
Two ways of pricing a route are tried - one that treats uphill as expensive, one that treats
gaining trench depth as expensive - because they find different ways round the same hill. That
search took the count from 6 down to **3**.

| Station | Ground | Depth | Lift | Rising main | Peak flow | Properties |
|---|---|---|---|---|---|---|
| MH-1024 | 364.4 m | 11.5 m | 10.2 m | 49 m DN200 | 10.4 L/s | 340 |
| MH-1488 | 355.6 m | 11.8 m | 10.7 m | 81 m DN200 | 9.0 L/s | 289 |
| MH-0687 | 364.1 m | 10.8 m | 10.5 m | 32 m DN200 | 7.3 L/s | 226 |

Why any pumping is needed at all: the main spine to the outfall is about 4.6 km long, and along
the way the ground **drops about 5 m and then climbs back over a ridge** before falling to the
outfall. A sewer cannot climb, so it goes deep under that ridge. It is not a shortage of fall
overall - there is about 14 m from the top of the spine down to the outfall, and the minimum
gradients need less than that. It is the shape of the ground in between.

All 3 stations sit within 1.5 km of one another, so detail design can look at whether
the upper ones should feed the lower one rather than each having its own discharge.

## Junctions

The guideline says no pipe may arrive at a chamber pointing back against the flow. Where a side
street met the main line at a bad angle, a **bend chamber** now goes a few metres short of the
junction, so the turn is made in two smaller steps instead of one sharp one - half of anything up
to 180 degrees is never more than 90. 172 of those were added.
131 junctions have no room for one - the bend chamber would sit inside
a plot, or too close to another chamber - and are marked `SWEPT_CH=1` in the manhole layer for a
purpose-made chamber with a curved channel.

## Another fault found on the way

The route search runs the whole design several times and keeps the best one. But the note saying
which pipe each plot joins is written onto the plot itself, so it always described the **last**
attempt, not the one we kept. The house-connection check was therefore looking at pipes that no
longer existed, and silently reported nothing at all. The joining is now redone on the design we
keep, and the check works again - which is why the long-connection failure has reappeared below.

## Where it stands

| | |
|---|---|
| Chambers / pipes | 1,925 / 1,924 |
| Sewer length | 78.7 km |
| Flow at the outfall | 3,619 m3/day average, 96 L/s peak |
| Deepest chamber | **11.88 m** against a 12.00 m limit |
| Pumping stations | 3, lifting 855 properties a total of 31.4 m |
| Rising mains | 162 m |
| Checks failing | 3 of 22 |

### The failing checks

1. **50 pipes arrive at a chamber at a sharp angle** where the street layout leaves no
   room to turn them. Each needs a purpose-made chamber with a curved channel - normal detail
   work, and they are marked in the outputs so the chamber schedule can pick them up.
2. **50 house connections run longer than 50 m.** These are plots whose only frontage
   is a dual carriageway. Since no pipe may be laid in one, they have no near street to join.
   They need either a sewer in the service road alongside or a local collector - that is your
   call, because it means relaxing the dual-carriageway rule in a limited way.
3. **2 branch sewers start closer than 10 m to a junction chamber** and should simply
   be merged into it on the drawing.

None of the three touches pipe sizes, gradients or levels.

## What to look at

| File | What it shows |
|---|---|
| `W6/shp/W6_pumping_stations.shp` | the stations, with depth, lift, rising main and duty flow |
| `W6/shp/W6_manholes.shp` | `IS_PUMP`, `LIFT_M`, `SWEPT_CH`, plus ground, invert and depth |
| `W6/shp/W6_pipes.shp` | `RISE_MAIN` marks the pumped pipes, `QDUTY_LS` their duty flow |
| `W6/img/W6_M2_depth.png` | how deep the pipes sit, with the stations marked |
| `W6/dxf/W6_test_boundary_design.dxf` | layers `SEW-PUMP`, `SEW-RISING-MAIN`, `SEW-SWEPT-CH` |
| `W6/run/audit_table.txt` | all 22 checks, pass or fail, with the guideline page |
| `W6/report/W6_Sewer_Network_Design.docx` | the full write-up |
