# Drops over 2 m — what removes them (study, 2026-11-18)

**A temporary study on the final design (0.75 %, 2056). The design, the SewerGEMS models and report R10 are not changed.**
Asked by the engineer on 2026-11-18: use the design engine to find workarounds for as many junction drops over 2 m as
possible, keep the record, build on the earlier discussion (`W17/assessment/junction_drops/`, October: reroute the deep
sewer, step the branch down in backdrops of 2 m or less, a parallel shallow sewer beside the deep one), add new ideas,
and say how many cannot be resolved and what to do with them.

PAM-GUD-203 p30: a backdrop when the invert drop exceeds 0.6 m, at most 2 m high; beyond 2 m a vortex drop shaft. So a
drop over 2 m is allowed, with a shaft; the aim is fewer shafts and less cost.

```
python drops_engine.py SC1-2056      # also SC2-2056, SC3-2056, SC4-2056
& "C:\Program Files\QGIS 3.44.8\bin\python-qgis-ltr.bat" drops_map.py SC1-2056
```
Per case `<case>/`: `drops.csv` (every drop over 2 m: role, height, receiving depth, branch length, ground downstream,
cost of each fix on its own, the vortex floor, the recommended fix, reconnection target), `variants.csv` (the whole
network under each variant), `summary.json`, `drops_<case>.gpkg` (layer `drops_over_2m`, EPSG:32640) and, for SC1,
`map_drops_SC1-2056.png`.

## How the engine works

It re-lays each case with the design engine's rule (`py/split_deep_subnetworks.relay`: from the heads down, cover 1.3 m
over the soffit, crowns matched) and checks it: with the laid gradients it reproduces the design's depths, 95 % within
5 mm. Then:

| Fix | What it does | Source |
|---|---|---|
| **F1 regrade** | A pipe on ground falling faster than its gradient steepens until its low end has cover, up to 4 % (NWS, 16 Sep 2026) and never past 3 m/s. | **New.** The design lays every pipe at its Table 11 (or self-cleansing) gradient from the cover at its low end, so on steep ground its high end hangs deep and the pipe above drops into it (P1-M3705: ground 9.6 %, pipe 0.51 %, 9.1 m drop). |
| **F2a steepen** | The branch's last pipe steepened (4 %, 3 m/s); if that is not enough, its upstream manhole lowered and the pipes above in turn, without any new backdrop. | Idea 2 (lower the branch), done by the engine. |
| **F2b step down** | As F2a, with new backdrops of 2 m at most at the branch's own manholes. | October idea 3. |
| **F2 above 4 %** | F1 + F2b with gradients allowed to the 3 m/s limit (capped at 15 %), where NWS accepts steeper than 4 %. | New. |
| **F4 reconnect** | The branch joined to another manhole within 100 m that is not upstream of it and low enough for a 0.5 % pipe and a drop of 2 m or less. Candidate only: the route is checked on the street plan. | New. |
| **F3 parallel** | A shallow sewer beside the deep one collects its drops and joins it once (drops on the same deep sewer within 300 m, on falling ground). | The engineer's October idea. |

Each drop is first costed on its own (F2 at 4 %, and at 3 m/s) at the BOQ rates (team's options cost estimate: sewers and
manholes by size and 0.5 m depth band). A vortex drop shaft has no rate in the estimate, so a fix counts as economic
when it costs less than a 1,800 mm manhole as deep as the receiving manhole, a floor for any shaft structure.
Recommended = the first of F1, F2 at 4 %, F2 above 4 %, F4, F3 that is economic or available; else a vortex shaft.
Manholes may go to 16.5 m (the design's cap); a lowering that would pass it fails.

## Results (2056 designs)

| | SC1 | SC2 | SC3 | SC4 |
|---|---|---|---|---|
| Drops over 2 m (manholes) | 1,301 (1,269) | 1,297 (1,265) | 1,306 (1,274) | 1,302 (1,270) |
| of which branch / main line | 1,136 / 165 | | | |
| F1 regrade | 51 | 51 | 51 | 51 |
| F2 lowered, gradients to 4 % | 1,224 | 1,217 | 1,233 | 1,226 |
| F2 lowered, gradients above 4 % (to 3 m/s) | 17 | 17 | 17 | 17 |
| F4 reconnect (candidate) | 2 | 3 | 0 | 1 |
| **Vortex drop shafts left** | **7** | **9** | **5** | **7** |

The whole network under each variant (SC1; the others within ±0.1 M OMR):

| Variant | Drops over 2 m | Backdrops 0.6–2 m | Manholes > 12 m | Cost change, M OMR | Under 0.75 m/s at 2031, km |
|---|---|---|---|---|---|
| Design as laid | 1,301 | 1,677 | 330 | – | 9.29 |
| F1 regrade, 4 % | 1,250 | 1,154 | 328 | −0.98 | 9.29 |
| F1 + F2a steepen only, 4 % | 7 | 2,397 | 335 | +1.52 | 9.09 |
| F1 + F2b steepen and step down, 4 % | 7 | 2,853 | 336 | +1.29 | 9.09 |
| F1 + F2b, gradients to 3 m/s | 0 | 2,402 | 328 | −0.24 | 9.09 |

- **F2 at 4 % costs little per drop:** median 330 OMR, 90 % under 3,900 OMR, at most 22,600 OMR; 1,224 drops, about 1.7 M OMR
  costed one by one (the whole-network run, which shares lowered pipes, nets +1.3 M OMR after F1's saving).
- **The 17 above 4 %** are one steep hillside line, P1-M3704 to P1-M3788 (DN200, ground falling up to about 10 %). At 4 % they
  would need manholes past 16.5 m or cost 13,000 to 257,000 OMR each; with gradients to 3 m/s they cost nothing.
- **The 7 shafts left in SC1** are all trunk junctions, DN900 to DN1600 (P1-M23, M67, M108, M151, M152, M1167, M4879), where a
  deep main is joined by a shallower one (drop 3.5 to 10 m). Lowering the shallower main costs 14,000 to 78,000 OMR each,
  above the 1,800 mm manhole floor but probably below a vortex shaft sized for a trunk flow: decide with a shaft price.
- **F4 candidates (SC1):** P1-M40 to P1-M2486 (50 m) and P1-M4833 to P1-M169 (48 m), both main-line drops on trunks; check
  the route on the street plan.
- **F3** found no group of two or more hard drops on falling ground: once F1 and F2 have done their work, the parallel
  sewer has nothing left to collect.
- Every resolved drop becomes a backdrop of 2 m; backdrops rise from 1,677 to about 2,400 (3 m/s) or 2,850 (4 %). **The
  BOQ has no item for backdrops or vortex shafts**; both need one.
- No pipe passes 3 m/s; self-cleansing improves slightly (9.29 → 9.09 km under 0.75 m/s at 2031); station depths unchanged.

## What to decide

1. Adopt F1 in the design engine (a pipe follows falling ground, to 4 %): it saves about 1 M OMR and removes 51 drops.
2. Lower the branches (F2) at the ~1,230 drops where it costs less than a shaft; the junction keeps a 2 m backdrop.
3. Ask NWS to accept gradients above 4 % (to the 3 m/s limit) on the P1-M37xx hillside: 17 drops, no cost.
4. Price a vortex drop shaft for trunk flows; then lower the shallower main or build the shaft at the 5 to 9 trunk junctions.
5. Add backdrops and vortex shafts to the BOQ.

The design change itself (1, 2, 3) is a new iteration of the design and the SewerGEMS models, not part of this study.

**Decision (engineer, 2026-11-18): leave it as a study, kept on record.** The design, models and report stay as they are; the fixes above are not applied.
