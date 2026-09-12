# W13/tmp3 — W13 temp 3, the work goes on from temp 2 (2026-09-09)

A clone of `W13/tmp2`, the constructable layout the engineer accepted on 2026-09-09. `tmp2` is
frozen as the record; every change from here is made in this folder. Its logic is `docs/W13_TMP3_DESIGN_LOGIC.md`, which starts from tmp2's and carries the
rulings made since; a changed rule is rewritten with one dated line at its head.

The first run (2026-09-09) reproduces temp 2 to the digit: 42 sub-networks, sub mains
69.9 km, 2,637 chambers, deepest 16.36 m, 16 over 12 m. Rerun with `python run_stage_a.py`
from `py/`; it writes here only (`OUT` in `py/config_built.py`). QGIS group
`Claude W13 temp 3` with `tmp3 pipes by depth`.

Standing instructions for this folder (engineer, 2026-09-09):

- the parts of the route to the works below 12 m stay as they are, to be discussed later;
- subnetworks first; the overall network is checked when all of them are prepared;
- nothing is added to the logic without telling the engineer first.

**2026-09-11: the plots' own flows, the gradient grid and the self-cleansing audit.** Every
plot is W14's `PLOTS_load` (heads, served plots, the link test, the flow). Pipes sized on
`Q_ULT` (Merrimack above 100 properties, Peltier at or below, 720 l/d/km infiltration);
gradients at the Table 11 minimum, or rounded up to 0.05 % steps (0.025 % from DN500) where
the ground forces steeper; the audit on `Q_2030` × 0.61 classes every pipe velocity, tractive
or washing and changes nothing; `TIER` in the guideline's names, `ROLE` in the engine's.

| | tmp2 | tmp3 |
|---|---|---|
| plots loaded, of those with flow in the boundary | | 8,028 of 8,358 |
| sizing flow loaded, m³/d | 8,545 (flat 0.911 per property) | 9,042 of 9,618 |
| pipes on tmp2's, same role | | 99.7 % |
| deepest, over 12 m | 16.36 m, 16 | 16.38 m, 14 |
| velocity / tractive / washing, km | | 0.4 / 63.0 / 149.8 (70 % washing) |

One outlet moved: a 29 ha metered farm south of the works is agricultural in `PLOTS_load`
(built in W3's file), so a 120 m link to the main pipe may cross it and the 59 km around the
works now leaves by it; the main-pipe join is not floored, so that arrival is not checked.

**Accepted by the engineer on 2026-09-12 and frozen**: the plots' own flows, the gradient grid, the
audit and the QGIS style (`qgis/tmp3_pipes.qml`, widths and arrow sizes by ROLE, arrows mid-pipe).
The work goes on in `W13/tmp4`, a clone of this folder. The QGIS project is now `stp2.qgz`.
