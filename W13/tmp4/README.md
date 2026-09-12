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
- the stages are the engineer's (2026-09-12): **A** the layout (what runs today), **B** the hydraulic
  design of each subnetwork, **C** the whole network on the main pipe and the works; A runs alone
  for an area first, B with it or after it (`STAGE` in the config), C once every area is in. B is
  built here on the test boundary first, gated on reproducing A's layout.

Open with the engineer:

- **the pockets** (brainstorm pending): which header chamber the pump discharges to and the
  length cap; the pump rate (the pocket's peak, rising main 1.0 to 2.5 m/s); the station at the
  pocket's low junction; whether rule 9 of CLAUDE.md still holds (one station per pocket,
  cascade within 1.5 km, under 50 plots deferred); the rising main along the streets; what to
  report per station;
- **the metered farm south of the works**: agricultural in `PLOTS_load`, so a 120 m link to the
  main pipe crosses it and the 59 km around the works leaves by that link instead of the STP;
  its arrival at the main pipe is not checked (joins not floored);
- **stage B, step 1 built (2026-09-12)**: the real lay, chambers, the check at the laid
  gradient, crossings recorded (rules 11 to 15 of the logic; `STAGE = "AB"`, outputs
  `shp/W13_B_reaches.shp`, `shp/W13_B_chambers.shp`, `run/stage_a.json["stage_b"]`). On the test
  boundary: 3,614 reaches, 3,656 chambers, 133.6 km at Table 11 and 79.7 km steeper by cover,
  deepest chamber 16.8 m against stage A's 16.4, 32 chambers over 12 m, 570 backdrops of which
  272 over 2 m (laterals joining deep headers), no capacity failure, 150 reaches in a wadi, one
  dual-carriageway crossing. **Still to build in B**: the pumps as candidates (the brainstorm's
  answers are in), the SewerGEMS export (after C, or on request);
- **stage C, after every area has A and B**: the main pipe sized and laid, the joins floored on
  it, the connection to the works and the inlet, the pumps of the whole, the trunk crossings.

For the concept report (engineer, 2026-09-12):

- the **1.5 l/s design floor** on the peak flow for the tractive-force check, as our assumption
  (Mara's minimum flow; G203 gives none), to be changed if NWS disagrees;
- the **curve** `img/mara_curve.png`: Mara's minimum gradient at τ = 1 Pa against the Table 11
  minima, the floor marked, and where each pipe size's minimum meets the curve;
- no pipe is regraded for tractive force; a pipe bigger than DN200 carries `TRAC_OVER` instead.
