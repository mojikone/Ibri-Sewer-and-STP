---
name: qgis-mcp-relay-fallback
description: When the qgis MCP relay hangs (calls return "Server qgis unavailable" while the app says connected), talk to the plugin's socket directly with W16/report_basis/qgis_direct.py
metadata:
  type: reference
---

The qgis MCP relay (uvx qgis-mcp-server, spawned at session start) hung on 2026-09-14 after a
68-panel render that outran its timeout; every later call returned "Server qgis unavailable"
although the app reported the connector connected, and the app's reconnect refuses a server
that is not "failed". QGIS itself was fine. The plugin (qgis_mcp_plugin 0.14) listens on
localhost:9876 with length-prefixed JSON `{"type": ..., "params": ...}`; `execute_code` is a
plain command (only refused inside `batch`).

**How to apply:** `python W16/report_basis/qgis_direct.py ping`, then `... file script.py` to exec
a script inside QGIS and get its stdout; or start a new session, which spawns a fresh relay.
Long renders (dozens of map exports) are better run in two or three calls than one.
See [[long-runs-detached]] and [[pyqgis-mcp-crash-dangling-symbol]].
