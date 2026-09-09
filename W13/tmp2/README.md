# W13/tmp2 — W13 temp 2, the constructable layout (2026-09-08)

A clone of W13's engine (the state of commit `8529df6`) laid the way the engineer described:
the outfall is the target, gravity is the way the streams go, sub mains first on the straight
roads, the smaller streets hung on them, nothing optimised, and the 12 m rule read as
"whatever cannot reach within 12 m remains a pocket". W13 itself and `tmp1` are untouched.
Rerun with `python run_stage_a.py` from `py/`; it writes here only (`OUT` in
`py/config_built.py`).

What differs from W13 (settings in the "W13 temp 2" block of `py/config_built.py`, code
marked "temp 2"):

- outlets by the flood, not the least-depth cost (`ASSIGN_BY_DEPTH = False`);
- the way out of a settlement is a designed pipe along the roads outside it
  (`ROAD_CORRIDOR`), one entry per settlement, the lowest; NAMA's line is not used;
- a pocket is taken out of the network (`assign_with_pockets` in `run_stage_a.py`): its
  lake below the spill level, and what is cut off behind it drains into it; a pocket floods
  nothing and pulls no neighbour in;
- a sub main stays on its own outlet's ground (`sub_mains_by_chains` in
  `sewnet/skeleton.py`): the boundary run into another catchment is left to be a branch,
  because a pocket's sub main had hoisted 40 km of the works' catchment into the pocket;
- no trunk is built for a pocket and no reroute (`POCKET_TRUNKS = False`,
  `REROUTE_MODE = "cut"`): after the lay, the deepest basin of a sub-network past 12 m is
  cut and the rest laid again, best round kept;
- sub mains cut at a crest, at a sag the water leaves, and at a change of outlet, with the
  250 m connector, as in W13.

Result (run of 2026-09-08 23:14): 42 sub-networks, one block each; sub mains 69.9 km,
laterals 93.2 km, branches 49.8 km; 2,637 chambers; deepest 16.36 m, 16 chambers over 12 m,
all in the two sub-networks that go to the works: the west settlement (41.1 km to the road
entry at (445199, 2566068), 11.1 m deep there, invert 323.07 m, so the road pipe arrives at
the works 3.5 m under the inlet at 323.0 m) and the settlement around the works (59.1 km,
arriving 10.7 m under). The cut rule does not reach them: their depth is on the way to the
works, whose inlet lies above their ground, not in a basin. One pocket by the flood rule, the
basin at (443413, 2566163), 10.7 m of fill, 7.5 km. Drawing `dxf/W13_A_tree.dxf`, numbers
`run/stage_a.json`, QGIS group `Claude W13 temp 2 (constructable layout)` with
`tmp2 pipes by depth`.
