# Where the network has to be pumped — W10 Phases 2 and 3, 2026-09-01

Three of the questions this stage was set up to answer are the same calculation: where
lifting stations are needed, whether the far south needs a big lift, and whether the
western area can be connected. All of them are answered by laying every corridor as shallow
as the cover rule allows and seeing where 12 m is reached anyway.

Method: the 2,279 km corridor-and-trunk graph, flow routed by a cost that charges heavily
for every metre CLIMBED in the direction of flow, then W8's lift-and-reset applied to the
whole network. Where depth would pass 12 m a station goes in, the sewage is raised back to
normal cover, and the pipe restarts on gravity. Depth is checked **between** nodes as well
as at them — 82,187 terrain samples at 20 m spacing — because corridor nodes sit about
100 m apart and a ridge halfway along a reach is exactly what a node-only check misses.
That omission is what let the W6 audit pass chambers at 21 m.

## The answer depends on the gradient, and the gradient is not settled yet

| Minimum gradient | Depth breaches | Total lift | Deepest | Median cover |
|---|---|---|---|---|
| 0.10 % | 77 | 986 m | 11.99 m | 1.70 m |
| 0.20 % | 104 | 1,367 m | 12.00 m | 1.79 m |
| **0.30 %** | **140** | **1,832 m** | 11.97 m | 1.88 m |
| 0.50 % | 254 | 3,230 m | 11.99 m | 2.06 m |

The count more than triples across the range. That is the single most important thing on
this page: **the pumping bill is decided by pipe sizing, not by topography.** A gradient is
a consequence of a diameter and a flow, and neither is settled until the load allocation
lands. Any station count quoted before then is a sensitivity, not a design.

0.30 % is carried forward for mapping because it is the mid-case, not because it is right.

## 140 breaches are not 140 stations

A breach is a point where the pipe would pass 12 m. Several breaches a few hundred metres
apart are one station, and the rule for that is already settled (CLAUDE.md rule 9: stations
within 1.5 km are cascade candidates, pockets under 50 plots are absorbed into detail
design). Applying it:

| Consolidation radius | Stations |
|---|---|
| none (raw breaches) | 140 |
| 500 m | 100 |
| 1,000 m | 64 |
| **1,500 m (rule 9)** | **37** |
| 2,500 m | 13 |

Of those 37, **9 serve fewer than 50 plots** and are absorbed. So the working figure is

> **28 lifting stations for 2,279 km of network serving about 60,000 plots.**

122 of the 140 raw breaches sit within 1.5 km of another, median separation 533 m, which is
why the consolidation is so large. The 50 breaches serving under 50 plots between them
carry 764 m of the 1,832 m total lift — a lot of pumping for very few properties, and the
first place to look when the design is optimised.

## Moving the works south barely changes the pumping

Running the identical solve with the whole network draining to the southern site instead:

| Outlet | Stations (raw breaches) | Total lift |
|---|---|---|
| Existing works, 328.7 m | 140 | 1,832 m |
| Proposed southern site, 311.7 m | 129 | 1,690 m |

**An 8 % improvement, not a transformation.** This corrects the impression left by the
Phase 0.4 audit, where straight-line routes made the southern site look decisive. On real
corridors it is a modest gain. The reason is that the 17.3 m of extra fall helps the
network near the works and does nothing for the eastern arms 30 km away, which is where
most of the pumping is.

The southern site's case therefore rests on the two specific things Phase 0.4 found — it
gives the western area a workable gravity gradient where the existing works cannot, and it
turns a 17 m lift for the southern plots into a fall — plus whatever the siting study says
about land, buffer and expansion. It does **not** rest on a network-wide pumping saving.

## The western area

Subnetwork 22 is the north-west: **68.1 km of corridor serving 117 plots**, with breaches
along most of it and a deepest chamber of 11.4 m. That is 580 m of sewer per plot, against
a network average of about 36 m. Whatever the right answer is for the north-west, a gravity
connection to the main network is not obviously it, and this is the clearest candidate in
the whole study area for a decentralised solution. It is carried into the Phase 4 options
rather than resolved here.

Note this is a different thing from the western leg of the MAIN PIPE, which is the 7.86 km
disconnected component dealt with in `MAIN_PIPE_AUDIT.md`.

## What is not settled

- **Diameters and therefore real gradients.** Everything above is on a uniform assumed
  minimum gradient and a nominal 300 mm outside diameter. The load allocation replaces both.
- **Lift heights** read median 11.6 m and maximum 42.8 m, but the median is an artefact of
  the construction: a station triggers at 12 m and resets to about 1.6 m cover, so roughly
  10.4 m is the smallest lift the method can produce. Real duty comes from the station
  design, not from this.
- **Station siting** is at the breach point, which is a hydraulic position, not a land
  parcel. Each one needs a site.
- **Cascading** between the 122 stations within 1.5 km of each other is identified, not
  designed.

## Outputs

`W10/py/p2_depths.py` · `W10/shp/W10_nodes_depth.shp` (ground, invert, depth on 20,937
nodes) · `W10/shp/W10_lift_stations.shp` (140 breaches) ·
`W10/shp/W10_lift_consolidated.shp` (37 consolidated) · `W10/run/p2_depth_sweep.csv` ·
`W10/run/p2_outlet_comparison.csv` · figure `W10/img/W10_P2_depths.png`.
