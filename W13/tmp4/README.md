# W13/tmp4 — W13 temp 4, the work goes on from temp 3 (2026-09-12)

A clone of `W13/tmp3`, which the engineer accepted on 2026-09-12 with the plots' own flows,
the gradient grid, the self-cleansing audit and the QGIS style. `tmp2` (2026-09-09) and
`tmp3` (2026-09-12) are frozen as the record; every change from here is made in this folder.
Its logic is `docs/W13_TMP4_DESIGN_LOGIC.md`, which starts from tmp3's; a changed rule is
rewritten with one dated line at its head, after the engineer agrees.

Rerun with `python run_stage_a.py` from `py/`; it writes here only (`OUT` in
`py/config_built.py`). Check the layout against the last accepted folder with
`python gate_vs_ref.py tmp3` (or `tmp2`). The first run reproduces temp 3 to the digit.

QGIS: the project is now `Hydraulic/QGIS/QGIS 2621 ibri sewer stp2.qgz` (the engineer
rebuilt it on 2026-09-12 after three crashes caused by a PyQGIS call of mine; the older
`stp.qgz` is kept). Group `Claude W13 temp 4`; the pipe style is `qgis/tmp4_pipes.qml`
(widths and arrow sizes by ROLE, arrows mid-pipe), applied with the built-in style call, never
by editing symbols in place.

Standing instructions for this folder (engineer, 2026-09-09 to 2026-09-12):

- the parts of the route to the works below 12 m stay as they are, to be discussed later;
- subnetworks first; the overall network and the main pipe are sized when all are prepared;
- nothing is added to the logic without telling the engineer first;
- no tertiary at the concept stage; every line in the DXF is usable, the draftsman's
  crossings are the only crossings; areas are done one at a time, each focused;
- Stage C is built here on the test boundary first, gated on reproducing the accepted layout,
  then each area gets A, B and C in one run.

Open with the engineer:

- **the pockets** (brainstorm pending): which header chamber the pump discharges to and the
  length cap; the pump rate (the pocket's peak, rising main 1.0 to 2.5 m/s); the station at the
  pocket's low junction; whether rule 9 of CLAUDE.md still holds (one station per pocket,
  cascade within 1.5 km, under 50 plots deferred); the rising main along the streets; what to
  report per station;
- **the metered farm south of the works**: agricultural in `PLOTS_load`, so a 120 m link to the
  main pipe crosses it and the 59 km around the works leaves by that link instead of the STP;
  its arrival at the main pipe is not checked (joins not floored);
- **Stage C, still to build**: the real lay (three gradient bands, one gradient between
  chambers, drops), chambers and Table 12 spacing, the hydraulic check with SewerGEMS as the
  referee, the overall network and the inlet, pumps and rising mains, crossings.
