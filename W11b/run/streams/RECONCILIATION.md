# W11b - the stream network: which source the design follows

_measured 2026-09-03T12:59:11_

## The answer

**Use the 40,000 m2 (4 ha) network derived here: the engineer's own 0.5 km2 layer is the same network with orders 1-2 removed and it confirms 91-97 % of everything we call order 3 or above, but on its own it finds only 54% of the 50-year wadi skeleton against our 92%.**

## What was measured

| | ours (4 ha, 0.5 m terrain @ 5 m) | engineer, 0.5 km2, 4 m NSA DEM | engineer, pre-clipped DEM |
|---|---|---|---|
| length in the window | 7,533 km | 2,434 km | 5,574 km |
| threshold recovered from our own field | 0.046 km2 (declared 0.040) | 0.516 km2 (stated 0.5) | 0.015 km2 |
| recall of the 10-yr wadi skeleton (100 m) | 0.946 | 0.574 | 0.467 |
| recall of the 25-yr wadi skeleton (100 m) | 0.927 | 0.547 | 0.441 |
| recall of the 50-yr wadi skeleton (100 m) | 0.916 | 0.536 | 0.431 |
| recall of the 100-yr wadi skeleton (100 m) | 0.906 | 0.518 | 0.418 |
| recall of the 500-yr wadi skeleton (100 m) | 0.898 | 0.494 | 0.408 |

## Confirmation of our links by the engineer's network

| Strahler order | km | confirmed within 100 m |
|---|---|---|
| 1 | 3,772 | 28% |
| 2 | 1,917 | 47% |
| 3 | 960 | 91% |
| 4 | 471 | 95% |
| 5 | 190 | 97% |
| 6 | 145 | 92% |
| 7 | 46 | 97% |
| 8 | 31 | 97% |

Confirmation jumps between order 2 and order 3. That is why `MAIN_WADI_MIN_ORDER = 3` is a measurement and not a preference.

## Rejected

`Streams NSA 2m project boundary.shp` - extracted from a PRE-CLIPPED DEM, so contributing area is truncated for every wadi entering the study area from outside. It is denser than ours and still finds fewer wadis (43% of the 50-year skeleton against our 92%), and only ~21 % of it lies within 25 m of the engineer's own full-DEM extraction. A denser network that finds fewer wadis is a network in the wrong places.

## Defects found elsewhere (reported, not fixed - other agents own those files)

1. terrain.NSA_STREAMS points at the PRE-CLIPPED layer, so terrain.verify_vs_nsa_streams() is checking against the wrong file. It should point at 'Streams NSA 2m.shp'.
2. terrain.stage_streams writes ACC_M2 as the PEAK accumulation over all vertices of a link. The last vertex sits on the junction cell, whose accumulation already includes the receiving stem, so order-1 links carry areas up to 1,168 km2. This module re-derives it one cell back from the downstream end; after that no link is below the threshold that created it.
3. contract.STREAMS documents GND_FALL as 'ground fall', and its cross-field check reads a negative value as a reversed flow direction. On a bare-earth DEM 1.37 % of links have a negative RAW fall from real pits, not from reversed direction. This module publishes GND_FALL from the CONDITIONED routing surface (monotone by construction, and the surface the direction was derived from) and FALL_DEM beside it, with PIT = 1 where the two disagree. Nothing is hidden, but the contract's wording should say which surface it means.

## Flags that travel with this layer

```
W11b STREAMS | grid R5 @ 5 m | EPSG:32640

TRACTIVE STRESS tau = 1 Pa - AN ASSUMPTION, NOT A GUIDELINE VALUE. PAM-GUD-203 sec 4.2.2.1 (p27) gives the equation Smin = K tau^1.23 Q^-0.461 and no numeric design tau (GAP-9). At tau = 1.0 Pa the required gradients are the shallowest the method allows, so the pipes are shallower and the stations fewer. If NWS return tau = 2.0 Pa every tractive-governed gradient rises by 2.346x and every level downstream of it changes.

WADI TEST: AR&R flood-hazard class [4, 5, 6] of the 50-year grid. A PROJECT ASSUMPTION standing in for G203-p30 4.4.1's washout criterion, not a guideline threshold.
FLOOD NO-DATA IS READ AS DRY HIGH GROUND (engineer, 2026-09-03). 55 % of this window is outside the 50-year grid, so IS_WADI = 0 there means NOT SHOWN TO BE WADI. HAZ_COV on every row says which. NWS still owe full-coverage mapping.
STREAM THRESHOLD: 40,000 m2 (4 ha), MEASURED - the coarsest contributing area that still recovers >= 90 % of the 50-year hazard skeleton. See reconcile.json.
```
