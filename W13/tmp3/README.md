# W13/tmp3 — W13 temp 3, the work goes on from temp 2 (2026-09-09)

A clone of `W13/tmp2`, the constructable layout the engineer accepted on 2026-09-09. `tmp2` is
frozen as the record; every change from here is made in this folder. The logic it starts from
is `docs/W13_TMP2_DESIGN_LOGIC.md`, the same file as in `tmp2/docs`; when a rule changes here,
the rule is rewritten there with one dated line at its head, after the engineer agrees.

The first run (2026-09-09) reproduces temp 2 to the digit: 42 sub-networks, sub mains
69.9 km, 2,637 chambers, deepest 16.36 m, 16 over 12 m. Rerun with `python run_stage_a.py`
from `py/`; it writes here only (`OUT` in `py/config_built.py`). QGIS group
`Claude W13 temp 3` with `tmp3 pipes by depth`.

Standing instructions for this folder (engineer, 2026-09-09):

- the parts of the route to the works below 12 m stay as they are, to be discussed later;
- subnetworks first; the overall network is checked when all of them are prepared;
- nothing is added to the logic without telling the engineer first.
