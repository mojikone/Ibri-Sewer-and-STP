---
name: w18-split-deep-subnetworks
description: "Engineer's rule (2026-11-17) for subnetworks that go below 12 m after steepening for self-cleansing - cut, lift, join by gravity, fewest stations"
metadata:
  node_type: memory
  type: project
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-18T11:31:45.621Z
---

These are the engineer's rules for splitting deep subnetworks (2026-11-17). The tool is `W18…/py/split_deep_subnetworks.py`.

1. **Purpose and scope.** The aim is self-cleansing. Pipes above DN200 are steepened until they reach 0.75 m/s at the 2031 peak, up to a gradient limit (1 % proposed). This applies to every subnetwork.
2. **When to cut.** Cut only where a subnetwork stays deeper than 12 m all the way to its outfall. Deep stretches that come back to 12 m or less are left alone.
3. **Where to cut.** The cut goes at the last manhole that is 12 m deep or less. That manhole becomes a pumping station, which is a new outfall. Its flow is lifted to the next manhole, which restarts as a head at minimum cover: 1.3 m over the soffit, about 1.5 m invert depth for DN200.
4. **Gravity joins.** An outfall that ends at 12 m or less can join its receiving manhole by gravity instead of pumping. This applies only when the receiving manhole is within one standard manhole spacing (G203 Table 12: 100, 120, 150 or 200 m by pipe size). A long force main stays a pump.
5. **Re-laying after a join.** A join re-lays the receiving subnetwork, which may need a new cut. Keep repeating until nothing changes. The goal is the fewest stations; pumps come later at the cut points.
6. **Recovery stays inside the subnetwork (my addition, accepted by the engineer 2026-11-17).** A deep stretch only counts as recovering if it comes back within its own subnetwork. Without this, a gravity join let a 25 m deep sewer run for kilometres into the next subnetwork.
7. **An outfall is never moved (engineer, 2026-11-18).** A cut is a split of the network. No cut is made on the last pipe into an outfall that is still one (station or plant inlet); a deep outfall keeps its depth. The 2026-11-17 "moved one manhole up" for O20/O23 was called nonsense and withdrawn.
8. **Successive pipes in a street keep one gradient (2026-11-18).** Street run = at each manhole the arriving pipe of the same size within 30 degrees of the leaving pipe's line. Run gradient = the steepest any pipe above DN200 in it needs for 0.75 m/s at 2031, within the limit; each pipe takes the steeper of that and its laid gradient.
9. **Check velocity under 3.0 m/s at the design flow (G203 p27) and show any over it on the maps (2026-11-18).**
10. **Velocity is SewerGEMS's own, scaled by Colebrook-White for a changed gradient; outfall ground comes from the model's outfalls** (W17 S1.gpkg). With that, the re-lay reproduces SewerGEMS exactly.
11. **He checks with the team on the re-lay maps before anything goes into SewerGEMS.** Results and maps: `results/sc1_conditions/`, added to the QGIS project he was sent (`py/qgis_sc1_conditions.py`). 
12. **O14 and O11 are kept deep, uncut (engineer, 2026-11-18)**: their cuts only moved the station a few manholes up (`KEEP_DEEP` in the tool). A gravity join may not deepen an outfall kept uncut (O12 into O11 would take O11 from 12.4 to 15.0 m). Result: as designed 23 stations; up to 0.50 % 25, 0.75 % 27, 1.00 % 29.
13. **Team's review (2026-11-18): 1 % gives too many lifts; they looked at 0.50 % with SC1 designed for 2051** (job 076, R6). The result was 25 stations and 13.2 % of the length above DN200 under 0.75 m/s, against 25 and 17.4 % for 2056, so no station is saved. The 2051 pipes exceed the d/D limit in 2056 on about 22-52 km.
14. **`py/own_design.py` reproduces SewerGEMS's SC1 design without the model.** Its flows, sizes, stations and velocities all match, checked blind for 2051. It works only if the catalogue holds every size: DN1200 is on no 2056 pipe. SewerGEMS sizes each pipe at the gradient of its current size and starts from the modeller's sizes, so its answer depends on that start (63 pipes). A design check can therefore run on the host in seconds, while the model stays the record.
15. **The engineer looked at merging stations (2026-11-18, 2056 at 0.50 %; `py/whatif_merge_stations.py`).** O12's two stations do not come from the steepening: O12 is 14.56 m deep in the SewerGEMS design itself. They sit on two DN200 branches about 1 km apart and cannot merge; without them O12 is 14.6 m. O9-M103 and O9-M89 are in series, 1.26 km of sewer apart, and merge into one station at O9-M101, 12.6 m deep. A station the split places on a DN200 lateral exists because that lateral governs the depth of the trunk below it. Before questioning a station, check the design depth, `base_depth`. O9-M773 and O9-M728 cannot merge: they are in series, 4.1 km of sewer apart. M728 is caused by the steepened run below it; leaving that run's first 1.25 km at the design gradient removes M728.
16. **The engineer's decisions at 0.50 % (2056), 2026-11-18:**
   - O12 is kept deep (14.6 m) with no new stations.
   - O9-M103 and O9-M89 become one station at O9-M101 (12.6 m).
   - O9-M728 is removed and O9-M773 kept, leaving O9 at 14.3 m. He wrote "only O9-M728" but quoted this case's numbers.
   - Result: 21 stations, 321 manholes deeper than 12 m.
   - Self-cleansing is unchanged at 26.4 km (17.4 %), because the station choice never moves a gradient.
   - Not yet in `split_deep_subnetworks.py` (`KEEP_DEEP` plus merges), the maps or SewerGEMS.
17. **His logic, learnt and applied at every limit (engineer: "learn from my logic", 2026-11-18):**
   - `py/reduce_stations.py` drops a station, or merges two into one at any manhole both flows pass, as long as:
     - every new station is 12.65 m deep or less;
     - every outfall is 14.65 m deep or less;
     - no manhole is deeper than 16.5 m.
   - Those limits are the deepest values he accepted. The third one stops two drops (O9-M72, O9-M69) that would leave a 21 m manhole.
   - At 0.50 % the rule reproduces his own choice exactly.
   - The station sets go into `FIXED` in `split_deep_subnetworks.py`, keyed by scenario and limit; `--no-fixed` gives the split as searched.
   - Result: 21 / 23 / 25 stations at 0.50 / 0.75 / 1.00 %. Self-cleansing stays 17.4 / 6.1 / 1.9 %.
   - Results are in `results/sc1_conditions/C#_*_fewer_stations/`; the QGIS project shows these runs.
   - **Trap:** a split run into a folder whose GeoPackage QGIS holds open writes the CSVs and JSON, then fails on the GeoPackage. Write to a new folder, or restore the CSVs and JSON from git afterwards.

**Why:** steepening to 1 % for self-cleansing deepens the lower reaches of the subnetworks. The engineer prefers pumping stations to deep sewers.

**How to apply:** run the tool on a scenario's exports before changing the model, and show the engineer the map and the station count for each limit. Related: [[w18-growth-plot-rule]], [[sewergems-new-year-alternative-copy]].
