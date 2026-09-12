---
name: long-runs-detached
description: A whole-network engine run takes far longer than the 10-minute Bash cap; launch it detached with PowerShell Start-Process and watch its console file with Monitor
metadata: 
  node_type: memory
  type: project
  originSessionId: 19f33d71-40f1-4a1e-a505-44b3492908a2
  modified: 2026-09-12T18:20:19.092Z
---

The W15 stage A run over every DXF street (1,822 km of street, 12,870 runs) reads the ground
in ~100 s and then spends minutes in the streams picture and the 12 m rounds; the test
boundary took 65 s. Bash `run_in_background` kills a command at 10 minutes (600000 ms), so
the first whole-network launch on 2026-09-12 had to be stopped and relaunched.

**Why:** a killed run leaves half-written shapefiles and no error, and the engineer waits for
nothing.

**How to apply:** launch with `Start-Process python -ArgumentList run_stage_a.py
-WorkingDirectory <py> -RedirectStandardOutput <run/console_x.txt> -PassThru -WindowStyle
Hidden`, note the pid, then `Monitor` a bash loop that prints new step headers, Traceback,
MemoryError and `done:` from the console file and exits on them (timeout up to 3600000 ms).
The machine has 126 GB RAM; the whole-area run sat at 7 to 9 GB in the streams step, fine.
Release the QGIS group holding the output shapefiles before any run. See
[[pyqgis-mcp-crash-dangling-symbol]].
