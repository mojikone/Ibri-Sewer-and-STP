---
name: pyqgis-mcp-crash-dangling-symbol
description: "QGIS aborts when PyQGIS chains renderer().categories()[i].symbol() in one expression; bind the list and category to names, or style through a QML file"
metadata: 
  node_type: memory
  type: feedback
  originSessionId: 19f33d71-40f1-4a1e-a505-44b3492908a2
  modified: 2026-09-12T07:13:18.291Z
---

Three QGIS crashes on 2026-09-12 (qgis-python-crash-info files in %LOCALAPPDATA%\Temp) all
died on the same line shape: `r.categories()[0].symbol().symbolLayers()` (or `.clone()`).
`categories()` returns a copy of the list; `[0]` is a temporary category; `.symbol()` is a
raw pointer into it; the temporary is freed before the next call, and QGIS aborts. The
same code with `cats = r.categories(); c = cats[0]; sym = c.symbol()` ran fine.

**Why:** the engineer loses his open QGIS session each time, has to relaunch and rebuild the
project, and reads the crash as "QGIS crashes the moment you start working in it".

**How to apply:** in `mcp__qgis__execute_code`, never chain a value-returning getter into a
pointer getter. Bind every intermediate (`cats`, `cat`, `sym`) to a name and keep it alive;
modify renderer symbols through `updateCategorySymbol(i, sym_clone)`, not on the copies
`categories()` returns; prefer the QML route for style changes (`save_style_qml`, edit the
XML text, `apply_style_qml`), which touches no C++ lifetime at all. Save the project in a
separate call after the change is confirmed. See [[show-drawings-not-tables]].
