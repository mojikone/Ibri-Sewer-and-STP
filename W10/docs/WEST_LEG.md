# The western area — W10 Phase 5, 2026-09-01

You said the western part of the main pipe is not connected to the rest because of a
topographic and gravity difference, and left the decision to me for this round. The
measurement is stronger than "not connected", and it settles the question.

## The western area is a closed basin

From its low point at 442092 E 2569064 N, ground 332.91 m, every route out crosses the
same high point:

| Route towards | Length | Highest point on the route | Above the start |
|---|---|---|---|
| the existing works | 13.23 km | 344.83 m at chainage 6.24 km | **11.93 m** |
| the proposed southern site | 16.92 km | 344.83 m at chainage 6.24 km | **11.93 m** |
| the nearest point on the main trunk | 7.09 km | 344.83 m at chainage 6.24 km | **11.93 m** |

It is the **same saddle** on all three. Not three separate obstacles — one, and every way
out goes over it. That is what makes it a decision rather than a routing problem: **which
works the west is sent to cannot change the outcome, because the constraint is 6 km from
the west and nothing to do with the destination.**

This is why all three came back "cannot be laid at any gradient inside 12 m". A route that
fails at *every* gradient, including a nominally flat one, is not failing on gradient. The
ground is above the pipe, and the height it rises is the lift that has to be paid whatever
else is decided.

## This corrects Phase 0.4

The main pipe audit tested the same journeys on **straight lines** and concluded the
southern works site solved the west by gravity at 0.200 % while the existing works failed
on velocity at 0.053 %. That conclusion does not survive the corridor test:

| | Straight line | On corridors |
|---|---|---|
| West → existing works | 6.18 km, 0.053 % | 13.23 km, 0.032 % |
| West → southern site | 10.13 km, 0.200 % | 16.92 km, 0.130 % |

The corridor routes are 2.1 and 1.7 times longer, so the available gradients fall by the
same factor — and both cross the saddle a straight line flies over. The audit flagged this
risk explicitly ("real routes are longer, flatter and deeper, and 9.6 to 10.5 m has little
margin against 12 m"); this is that risk landing.

**The southern site's case for the west is withdrawn.** Its case for the southern plots
still stands, and Phase 2 separately measured its network-wide pumping benefit at 8 %.

## So the west is pumped, or it is separate

| Option | What it costs |
|---|---|
| **A — lift at the west low point** | About 12 m of static lift plus cover, so roughly 14 m, then a rising main over the saddle. To the main trunk that is 5.97 km of rising main and 9.46 m of static lift to the trunk invert |
| **D — a local satellite works** | Avoids the lift entirely. Within 6 km of the west low point there are **403.1 km of corridor and 11,254 plots**, which is a real plant, not a package unit |

There is a second, deeper basin further south-west: the lowest corridor node within 9 km
sits at 307.11 m at 437135 E 2564721 N, **25.8 m below** the west low point. Reaching the
works from there needs 37.72 m of climb over 20.34 km, so it is a separate closed basin
again and a worse one. Anything draining that way is a third system, not part of either.

## Recommendation for this round

**Carry A and D as competing options, and expect D to win on the numbers.** 11,254 plots is
enough to justify a works of its own; a single lift with a 6 km rising main to serve them is
the kind of arrangement that looks cheap in capital and expensive for twenty-five years,
which is exactly the trap the PIAD review catalogued — annual operating cost multiplied by
25 and called a lifetime cost, with energy left at zero.

[Likely] on that ranking, not [Certain]: it needs the load allocation to size the satellite
works, the energy cost of the lift over 25 years at 5 %, and a site for the satellite works
from the Phase 4 siting study. All three are in hand and none of them is here yet.

## Not the same thing as the main pipe's western component

`MAIN_PIPE_AUDIT.md` deals with the 7.86 km disconnected component of the given trunk
drawing. This page is about the western drainage area it sits in. The component is a
drafting fact; the basin is a topographic one.

## Outputs

`W10/py/p5_west.py` · `W10/run/p5_west_options.csv` · route geometries
`W10/shp/W10_west_A.shp`, `_B.shp`, `_C.shp`.
