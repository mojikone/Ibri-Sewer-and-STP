# Checking the design engine against the network NAMA actually built

Written 20 August 2026, after the user asked for the engine to be measured against reality
rather than trusted.

Sources, all from `Data/Received/09-RECEIVED/NAMA/IBRI/WW/KMZ/`:

| File | What it holds |
|---|---|
| `SEWERLINE.kmz` | 3,322 gravity pipes, **188.6 km** |
| `FORCELINE.kmz` | 7 rising mains, **30.8 km** |
| `TE_LINE.kmz` | 6 treated-effluent lines, 49.4 km |
| `STP_PT.kmz` | existing STP (1,800 m³/d) and the design STP (29,038 m³/d) |

They are exported to `W7/shp/EXISTING_*.shp` by `py/export_existing.py`, which pulls the
attributes out of the HTML table inside each placemark.

**Read every number here as indicative.** The file carries its own warning: *"Data is not
reliable and must be used only for reference purpose."* `N_DIAMETER` is 0 on 3,267 of the
3,322 pipes, the depth columns are all zero, and one "pipe" is 10.5 km long. What IS usable
is the levels — upstream and downstream invert and ground on 3,267 pipes — and the geometry.

## What matches, and what does not

| Measure | NAMA as-built | W7 engine | Verdict |
|---|---|---|---|
| Median cover depth | 1.92 m | 1.75 m | matches |
| 90th percentile depth | 4.58 m | 5.02 m | matches |
| Deepest | 8.85 m | 10.02 m | mine digs deeper |
| Share deeper than 6 m | 1.4 % | 6.1 % | **mine digs deeper more often** |
| Median laid gradient | 4.98 mm/m | 5.00 mm/m | matches almost exactly |
| Median manhole spacing | 29.8 m | 43.4 m | **mine is wider** |
| 90th percentile spacing | 38.3 m | 80.0 m | **mine is much wider** |
| Pipes along a dual carriageway | 0.1 % (4 of 3,267) | 15 head chambers | **mine is wrong** |

## The four things this actually teaches

### 1. The hydraulics are right
Median laid gradient 5.00 mm/m against 4.98 mm/m as built, and the depth distribution sits
almost on top of the real one up to the 90th percentile. The minimum-gradient logic and the
cover rules are behaving the way a real designer's did.

### 2. Wider manhole spacing costs nothing — a hypothesis that failed
The obvious reading of "they use 30 m, I use 43 m" is that tighter spacing lets the pipe
follow the ground and stay shallow. That was tested by re-running the whole design at five
spacing limits:

| Spacing cap | Chambers | Median depth | Deepest | Over 6 m |
|---|---|---|---|---|
| 100 m (current) | 1,870 | 1.75 m | 10.02 m | 6.1 % |
| 70 m | 2,112 | 1.79 m | 10.02 m | 6.6 % |
| 50 m | 2,507 | 1.77 m | 10.02 m | 7.1 % |
| 40 m | 2,924 | 1.78 m | 10.01 m | 6.9 % |
| 30 m | 3,602 | 1.80 m | 10.01 m | 7.4 % |

Depth does not improve. It gets very slightly worse, and the chamber count nearly doubles.
The reason is simple once seen: depth is set by how much fall the route needs against how
much the ground gives, and adding chambers changes neither. A pipe cannot climb back up
just because there is a chamber in the way.

**So the spacing difference is not a fault to copy.** The user's instruction to keep
manholes to the fewest necessary is better supported by this evidence than the as-built
habit is. `py/exp_spacing.py` reproduces the table.

### 3. The as-built is shallower because it PUMPS
30.8 km of rising main against 188.6 km of gravity sewer — about one metre in seven of that
system is pumped, through at least 7 rising mains. That is how it keeps almost everything
under 6 m.

The W7 test area needs no pumping at all, because the main pipe alignment the user drew
gives every part of town a short route to a trunk that is already low. The two designs made
opposite trades: the as-built bought shallow trenches with pumping stations, W7 gets shallow
trenches for free from a better trunk.

This also puts the 6.1 %-versus-1.4 % difference in perspective: it is not that W7 digs
recklessly, it is that W7 accepts a deeper trench instead of a pump, which is what the user
asked for.

### 4. The dual-carriageway rule is confirmed by practice, and my design breaks it
Of 3,267 as-built pipes, **4 run within 4 m of a dual carriageway — 0.1 %**. Inside the test
boundary it is 3 of 2,098. The rule the user gave is exactly what the real network does.

W7 still has **15 head chambers sitting on a dual carriageway**, down from 22 after the
twin-carriageway fix. That is a real defect, not a matter of taste, and the as-built proves
it. It is the top item to finish.

## One thing that needs the road file, not the engine

Only 35 % of as-built pipes sit within 5 m of a road centreline, and 34 % are more than 20 m
from ANY road in `SHP/Road centerline 2`. Either the real sewers run through back lanes and
open ground, or the road file is missing streets. The second is more likely — the user has a
draftsman adding the roads that were never drawn. Worth re-checking once that lands, because
the engine can only lay pipe where it has a corridor.

## What changes as a result

| | |
|---|---|
| Keep as they are | minimum gradients, cover rules, depth limit, the "fewest manholes" instruction |
| Fix | the 15 head chambers still on a dual carriageway |
| Do NOT copy | the as-built 30 m manhole spacing — measured, and it buys nothing |
| Re-check later | the sewer-to-road relationship, once the draftsman's roads arrive |
