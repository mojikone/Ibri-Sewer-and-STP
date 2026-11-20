# Junction drops grouped by the deep sewer they join — an experiment (2026-10-03)

**Not used by the design, the model or the report.** The engineer asked for it during the concept-report Q&A, to keep for later:
group the drops where a shallow branch joins a deeper sewer by the deep stretch they join, and check whether the
ground falls along each stretch. That tells which fix fits where: reroute the deep sewer (idea 1), step the branch
down in backdrops of 2 m or less (idea 3), or, if neither works, a shallow sewer beside the deep one that joins it
once (the engineer's idea).

```
python junction_drops.py S1
```
Reads option S1's 2070 design from the SewerGEMS model R9 as the bridge exported it
(`D:\VBOX\bridge\out\scen\S1\conduits_S1-2070.csv`, `manholes_S1-2070.csv`). Writes `S1/`:
`drops.csv` (every drop over 0.6 m), `stretches.csv` (every deep stretch with a branch drop over 2 m),
`summary.json`, and `junction_drops_S1.gpkg` (layers `deep_stretches` and `drops`, EPSG:32640) for QGIS.
Only S1 was run; the other options differ by a few drops (S4 and S6 checked by hand the same day).

## Results, S1

- **2,998 drops over 0.6 m**: 2,004 where a branch joins, 994 on the sewer's own line.
- **1,025 branch drops are over 2 m**, past the backdrop limit of G203 p30. They sit on **367 deep stretches**.
  173 stretches have one drop each; **27 stretches have 10 or more and carry 413 of the 1,025 (40 %)**.

| Ground along the deep stretch | Stretches | km | Drops over 2 m | What fits |
|---|---|---|---|---|
| Falls at 0.5 % or more | 106 | 33 | 161 | the parallel shallow sewer stays at about 1.5 m (median); its one drop into the deep sewer is 3.2 m (median) |
| Falls, but flatter than 0.5 % | 99 | 94 | 246 | a parallel sewer gets deeper as it goes: 2.7 m at the median, up to 11 m |
| Rises 0.5 m or more somewhere | 162 | 261 | **782 (76 %)** | the deep sewer is deep because it climbs: reroute |

Of the 162 that rise: 69 rise less than 1 m (221 drops), 89 rise 1 to 4 m (531 drops), 4 rise 4 to 7 m (30 drops).

Stepping the branch down (idea 3), backdrops of 2 m at most:

| Backdrops needed | 2 | 3 | 4 | 5–7 |
|---|---|---|---|---|
| Branch drops | 574 | 306 | 114 | 31 |

137 branches are too short to take all their steps before their head, and 3 would go past 12 m.

The deepest drop, 12.15 m at O20-M3, is a branch of 3 pipes; stepped down it needs 7 backdrops and goes 13 m deep.

## Read with care

- **A 200 mm sewer at its minimum gradient of 0.5 % falls faster than the large deep sewer beside it** (0.075 to
  0.2 %). On ground flatter than 0.5 % a long parallel sewer therefore ends up **below** the deep sewer it is meant
  to join (`parallel_final_drop_m` negative). The parallel sewer works on falling ground, or in short sections.
- "Rises" uses a 0.5 m tolerance, which is this experiment's choice. 69 of the 162 stretches rise less than 1 m, so a
  parallel sewer only a little deeper could still serve them.
- The parallel sewer is tried as **one pipe along the whole stretch**, ending at one junction, as the engineer
  described it. Splitting a long stretch into several shorter parallel sewers was not tried.
- The ground is the manhole ground stored in the SewerGEMS model.
- The flow direction at a junction: the incoming pipe with the largest 2070 flow continues the deep sewer, and every
  other incoming pipe is a branch. Thresholds and method are in the header of `junction_drops.py`.
