# W15 — the whole network (2026-09-12)

The main working folder from here on: a complete copy of `W13/tmp4`, the engine the engineer
accepted on 2026-09-12 (stage A the layout, stage B the hydraulic design of each subnetwork,
the pumps as candidates), now set for **the whole network**. `W13/tmp2`, `tmp3` and `tmp4` are
frozen as the record of how the engine was built and accepted on the test boundary.

**The area is every street the draftsman drew** (`AREA_MODE = "DXF"`): the DXF's 12,616 lines,
45 × 25 km, buffered 60 m; no boundary file, the towns being administrative while networks
follow gravity and roads (engineer). The test boundary is inside it and is laid again as part of
the whole, so a street cut short by the boundary gets its proper subnetwork. The settlements,
for the one-road-entry-per-settlement rule, are the dense parts of that area (20 ha and more).
The ground is read at **4 m** over the whole (2 m on the boundary runs), the streams at 8 m.

**The engineer's sub main guide** (`SHP/Main Pipe/Sub Main Pipe guide.shp`, four lines, 9.2 km,
drawn 2026-09-12 for the west, where the network struggles with gravity) is part of the network:
its lines are streets, forced sub mains in the direction drawn, tied to the main pipe at their
feet (a guide end within 100 m of the main pipe gets a straight connector), the join at each
foot always kept. Every street that reaches it by gravity hangs on it; the flood decides. South
of the main road the joins on the main pipe stand as before. The main pipe is the file as
redrawn (55 pieces, 83.5 km, two new west legs ending at the low point).

**The 2006 network is a reference only** until the survey data arrives; then it is modelled as
the as-built (engineer, 2026-09-12).

Stages, as ruled on 2026-09-12: **A** the layout, run first over the whole (`STAGE = "A"`); a
temporary run shows how the subnetworks converge on the main pipe and the works, the
subnetworks are grouped by that into major groups, and the QGIS groups follow those groups;
**B** each subnetwork's hydraulic design once the layout is accepted; **C** the whole on the
main pipe and the works.

**Google Earth**: `python export_kmz.py` (from `py/`) writes `kmz/W15_A_network.kmz` from the last run:
a folder per convergence group, a folder per subnetwork inside it (its outlet, its sub mains one
placemark each with size, gradient, flow and depth in the balloon, its laterals merged), one colour
per subnetwork with neighbours within 150 m coloured apart, sub mains thick, the main pipe yellow,
the guide magenta, the pockets' sink points in a folder of their own; three overlays off until
ticked (flow arrows on the sub mains, pipes deeper than 12 m, the group outlines).

Rerun with `python run_stage_a.py` from `py/`; it writes here only. The logic is
`docs/W15_DESIGN_LOGIC.md` (tmp4's, carried on; a changed rule is rewritten with one dated line
at its head). The pipe style is `qgis/W15_pipes.qml`.

Run log: see the dated rows in the repository `README.md` and `_BRAIN/00_CURRENT.md`.
