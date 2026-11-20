---
name: qgis-mcp-relay-fallback
description: "When the qgis MCP relay hangs (calls return \"Server qgis unavailable\" while the app says connected), talk to the plugin's socket directly with W16/report_basis/qgis_direct.py"
metadata:
  node_type: memory
  type: reference
  originSessionId: 57016b2a-e4dc-482e-953e-69a030c28ebf
  modified: 2026-11-18T09:45:36.868Z
---

The qgis MCP relay (uvx qgis-mcp-server, spawned at session start) hung on 2026-09-14 after a
68-panel render that outran its timeout; every later call returned "Server qgis unavailable"
although the app reported the connector connected, and the app's reconnect refuses a server
that is not "failed". QGIS itself was fine. The plugin (qgis_mcp_plugin 0.14) listens on
localhost:9876 with length-prefixed JSON `{"type": ..., "params": ...}`; `execute_code` is a
plain command (only refused inside `batch`).

The port is not always 9876. A second QGIS instance takes another port; the W18 project was on 9881 on 2026-11-18. `qgis_direct.py` reads the `QGIS_PORT` environment variable and defaults to 9876.

**How to apply:** `python W16/report_basis/qgis_direct.py ping`, then `... file script.py` to exec
a script inside QGIS and get its stdout; or start a new session, which spawns a fresh relay.
Long renders (dozens of map exports) are better run in two or three calls than one.
See [[long-runs-detached]] and [[pyqgis-mcp-crash-dangling-symbol]].
