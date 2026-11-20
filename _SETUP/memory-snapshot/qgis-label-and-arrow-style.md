---
name: qgis-label-and-arrow-style
description: "Engineer's QGIS style (2026-11-18): label size driven by map scale clamp(7, 8*25000/@map_scale, 36) with a fixed 0.8 mm buffer; flow arrows at pipe centres from 1:15,000 in"
metadata:
  node_type: memory
  type: feedback
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-18T13:16:33.883Z
---

The engineer set these in `W18_plot_flows.qgz` in a side session on 2026-11-18. Keep them in all QGIS work.

1. **Labels on every layer:** the size is in points and data-defined by `clamp(7, 8*25000/@map_scale, 36)`. That gives 8 pt at 1:25,000, 20 pt at 1:10,000 and up to 36 pt close in, never below 7. The buffer is a fixed 0.8 mm. No label has a scale-visibility limit. He rejected two earlier versions: fixed sizes, and sizes in map units with a 2.5 mm floor, which looked fixed and vanished when zoomed out.
2. **Flow direction on pipe layers:**
   - one 1.8 mm filled arrowhead at the centre of each pipe, in the pipe's class colour;
   - drawn by a geometry generator `if("flow_rev"=1, reverse($geometry), $geometry)` with a marker line at the central point;
   - enabled only at `@map_scale <= 15000`.
   - `flow_rev` = 1 where the drawn line runs against the flow. The upstream end is the end nearer the manhole with the higher SewerGEMS invert. On SC1-2056 that is 8,713 of 19,083 lines: the modeller drew them start to stop, and SewerGEMS runs start to stop uphill on 8,712 of them.
   - So far only on SC1 C0.

3. **Manholes, a layer he asked for on 2026-11-18:** style in `W18…/qgis/styles/manholes_depth.qml`.
   - White 1.6 mm circles with a dark outline; the layer shows only at 1:15,000 and closer.
   - The label is HTML: the name in bold, then the depth after the split on a second line in normal weight.
   - Labels show only at 1:10,000 and closer. Their size is `round(0.75*clamp(6, 7*10000/@map_scale, 28),1)`, smaller than rule 1 because there are thousands of them.
   - The QGIS script loads the QML onto each condition's `manholes` layer and keeps it out of the printed legend.

**Why:** fixed sizes were unreadable at both ends of the zoom range. Arrows everywhere filled the whole-network view.

**Trap (2026-11-18):** a script that rebuilds the .qgz on disk does not change the QGIS window that has the project open. Saving that window writes the old project over the rebuild, which a side session did once. After a rebuild, check the open window through `qgis_direct.py`: is `isDirty` false, and do the groups and sources match? If not, reload before anyone saves.

**How to apply:** `W18…/py/qgis_sc1_conditions.py` builds both (`scale_labels`, `arrow_symbol`, `ensure_flow_rev`). Reuse those helpers for new map scripts. The W18 QGIS instance listened on port 9881; `W16/report_basis/qgis_direct.py` reads `QGIS_PORT`. Related: [[pyqgis-mcp-crash-dangling-symbol]], [[show-drawings-not-tables]].
