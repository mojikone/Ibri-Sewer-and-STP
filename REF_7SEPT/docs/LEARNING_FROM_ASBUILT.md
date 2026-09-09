# What the built network taught, and what changed because of it

Written 21 August 2026. The user asked for the engine to learn how a real engineer designs,
using NAMA's as-built network inside the test boundary as the teacher — 2,101 pipes, 78.6 km.

## The thing that had been missed for days

The as-built manhole IDs are not just names. They encode the designer's own decomposition:

    5A-2-TM-MH185      package 5A-2, TRUNK MAIN, manhole 185
    5A-2-SM.2-MH391    package 5A-2, SUB MAIN 2, manhole 391
    5A-1-A49-MH3       package 5A-1, lateral zone A49, manhole 3

Read that way, the network inside the test area is three tiers:

| Tier | Length | Share | How many |
|---|---|---|---|
| Trunk main (TM) | 4.02 km | 5.1 % | 1 |
| Sub mains (SM.1 – SM.6) | ~4.0 km | 18.4 % | 6 |
| Laterals | 52.32 km | 66.5 % | 419, median 88 m |

And the connectivity, traced through the designer's own `US_MHID` / `DS_MHID` fields:

| Where each of the 419 lateral zones drains | Count |
|---|---|
| into **another lateral** | **381 (91 %)** |
| into a sub main | 27 |
| into the trunk main | 10 |

Sewage crosses a **median of 11 laterals** before it reaches a sub main. Every sub main
drains to the trunk main. So only about **16 things touch the trunk**: 6 sub mains and 10
laterals.

## Why the design looked nothing like it

W7 had **no sub-main tier at all**. Every catchment found its own way to the main pipe, so
30 things touched it and 14 of those carried fewer than 100 properties — one carried 3.

The earlier calibration (`W7/docs/CALIBRATION_vs_EXISTING.md`) compared gradients, depths,
manhole spacing and junctions per km. All of those matched, which is exactly why it was
misleading: **the hierarchy is invisible in every one of those measures.** Matching averages
said the hydraulics were right. It said nothing about whether the layout was buildable.

## What changed

The joins onto the main pipe are capped, and the cap was swept to find where the design
stops working. Measured on the current network:

| Cap | Joins built | Pumping stations | Deepest | Dual crossings |
|---|---|---|---|---|
| none | 31 | 0 | 9.12 m | 1 |
| 24 | 23 | 0 | 10.33 m | 1 |
| **20** | **19** | **0** | **10.33 m** | **1** |
| 16 | 14 | 1 | 11.79 m | 1 |
| 12 | 11 | 3 | 11.97 m | 2 |
| 8 | 8 | 3 | 11.97 m | 2 |
| 6 | 6 | 2 | 11.90 m | 15 |

Below 14 joins the network starts buying pumping stations, and below 8 it starts crossing
dual carriageways to consolidate — 15 of them, each needing trenchless work. So 19 is the
tightest structure that still runs entirely on gravity without cutting across carriageways.

The result now has the shape the as-built has:

| | As-built | W7 | W8 |
|---|---|---|---|
| Things touching the trunk | ~16 | 30 | **19** |
| Of those, carrying 100+ properties | 6 sub mains | 3 | **7** |
| Carrying under 25 properties | few | 10 | **4** |
| Trunk main share of length | 5.1 % | — | 8.4 % |
| Sub main share | 18.4 % | none labelled | 12.2 % |
| Lateral share | 66.5 % | — | 79.3 % |

Every pipe now carries a `TIER` field — `trunk main`, `sub main`, `lateral` — using the
as-built's own vocabulary, so the two can be compared directly on a map.

## Two defects the user found in the same review, both fixed

**Crossings of a dual carriageway.** The design reported one crossing; eight pipes were
actually crossing. The charge only applied to crossings this code *created*, so any ordinary
pipe that happened to cross paid nothing. And the one that was labelled sat 97 m from the
underpass, because the "free at an underpass" test used a 120 m radius. Now every pipe that
physically crosses is charged, and the underpass radius is 30 m. The pipe at the real
underpass (21 m away) is the one that carries the label.

**Chambers inside people's plots.** The plot-clearance rule only ever guarded *bend*
chambers, so junctions, heads and spacing chambers were free to land in a garden — 49 did,
one of them 4.8 m inside a 739 m² house plot. Every chamber is checked now, against every
plot rather than only the loaded ones, and any that lands inside is slid back along its own
pipe until it is clear. 48 found, 26 freed. The 22 that could not be freed sit where the
road centreline itself runs through a plot: that is a question for the road or cadastre
data, not something the design can solve, so they are reported rather than hidden.

## Still open

- 4 pipes cross a dual carriageway with no underpass available. Each needs trenchless work
  or a re-route; they are not hidden.
- 22 chambers cannot be freed from a plot because the street they sit on runs through it.
- The lateral-into-lateral chaining is a consequence of capping the joins rather than a rule
  in its own right. It produces the right shape here; whether it holds over the full study
  area is not yet tested.
