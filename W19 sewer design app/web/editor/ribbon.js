"use strict";
/* W19 v2 (2026-11-23, user trial F10): the ribbon interface, as SewerGEMS's (File, Home, Layout, Components, Analysis,
   Report, View, Tools, Help), collapsible to its tab row. It is the same editor: the ribbon's controls either ARE the
   editor's own controls (moved into the ribbon, so every handler and test id still works) or press them. Shown at /v2
   (or with ?ui=ribbon); the classic toolbar stays at /. */
const RIBBON = location.pathname.replace(/\/+$/, "") === "/v2" || /[?&]ui=ribbon\b/.test(location.search);

const RI = {                                                   // small line icons (stroke = currentColor)
  new: '<path d="M6 3h8l4 4v14H6z M14 3v4h4 M12 11v6 M9 14h6"/>', open: '<path d="M3 7h6l2 2h10v10H3z"/>', save: '<path d="M5 4h11l3 3v13H5z M8 4v5h7V4 M8 20v-6h8v6"/>',
  sample: '<path d="M4 5h16v14H4z M4 9h16 M9 9v10"/>', sg: '<circle cx="12" cy="12" r="8"/><path d="M8 12h8 M12 8v8"/>', undo: '<path d="M9 7L4 12l5 5 M4 12h11a5 5 0 010 10h-2"/>',
  redo: '<path d="M15 7l5 5-5 5 M20 12H9a5 5 0 000 10h2"/>', copy: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M4 16V4h12"/>', scen: '<path d="M4 6h16 M4 12h10 M4 18h6"/><circle cx="18" cy="16" r="3"/>',
  find: '<circle cx="11" cy="11" r="6"/><path d="M16 16l4 4"/>', del: '<path d="M6 6l12 12M18 6L6 18"/>', design: '<path d="M4 20l6-6 4 4 6-10"/><circle cx="10" cy="14" r="1.5"/>',
  run: '<path d="M7 5l12 7-12 7z"/>', check: '<path d="M5 12l4 4 10-10"/>', props: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M15 4v16"/>', bottom: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 14h18"/>',
  max: '<path d="M4 9V4h5 M20 9V4h-5 M4 15v5h5 M20 15v5h-5"/>', proto: '<rect x="4" y="4" width="7" height="7"/><circle cx="17" cy="7.5" r="3.5"/><path d="M4 18h16"/>', lib: '<path d="M5 4v16 M10 4v16 M15 5l4 15"/>',
  load: '<path d="M12 3v12 M7 10l5 5 5-5 M5 20h14"/>', peak: '<path d="M3 18c4 0 5-12 9-12s5 12 9 12"/>', infil: '<path d="M4 8h16 M7 12v4 M12 12v6 M17 12v4"/>', rain: '<path d="M7 15a4 4 0 01.5-8 5 5 0 019.5 1 3 3 0 01-.5 7z M9 18l-1 2 M13 18l-1 2"/>',
  units: '<path d="M4 18h16 M6 18v-4 M10 18v-7 M14 18v-4 M18 18v-7"/>', tbl: '<rect x="3" y="5" width="18" height="14" rx="1"/><path d="M3 10h18 M9 5v14"/>', prof: '<path d="M3 17l5-5 4 3 9-8 M3 21h18"/>',
  sum: '<path d="M5 19V9 M10 19V5 M15 19v-7 M20 19v-4"/>', hydro: '<path d="M3 19c3-10 5-14 7-14s3 8 11 14"/>', out: '<path d="M4 4h16v16H4z M8 9h8 M8 13h5"/>',
  exp: '<path d="M12 3v12 M7 8l5-5 5 5 M5 21h14"/>', imp: '<path d="M12 15V3 M7 10l5 5 5-5 M5 21h14"/>', sym: '<circle cx="8" cy="8" r="3"/><circle cx="16" cy="16" r="3"/><path d="M14 6h6 M4 18h6"/>',
  fit: '<path d="M4 9V4h5 M20 9V4h-5 M4 15v5h5 M20 15v5h-5 M9 12h6"/>', zsel: '<circle cx="11" cy="11" r="6"/><path d="M16 16l4 4 M9 11h4"/>', theme: '<path d="M20 14.5A8 8 0 019.5 4 8 8 0 1020 14.5z"/>',
  keys: '<rect x="3" y="6" width="18" height="12" rx="2"/><path d="M7 10h1 M11 10h1 M15 10h1 M8 14h8"/>', up: '<path d="M12 20V5 M6 11l6-6 6 6"/>', down: '<path d="M12 4v15 M6 13l6 6 6-6"/>',
  rev: '<path d="M4 8h14l-3-3 M20 16H6l3 3"/>', recon: '<circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 12l10-5 M7 12l10 5" stroke-dasharray="2 2"/>',
  morph: '<circle cx="7" cy="12" r="4"/><rect x="14" y="8" width="8" height="8"/><path d="M11 12h3"/>', legend: '<path d="M4 6h3 M4 12h3 M4 18h3 M10 6h10 M10 12h10 M10 18h10"/>', layers: '<path d="M3 7l9-4 9 4-9 4z M3 12l9 4 9-4 M3 17l9 4 9-4"/>',
  asst: '<path d="M4 5h16v11H9l-5 4z"/>', classic: '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M3 9h18 M8 9v11"/>', measure: '<path d="M3 17L17 3l4 4L7 21z M7 13l2 2M10 10l2 2M13 7l2 2"/>',
  storm: '<path d="M7 13a4 4 0 01.5-8 5 5 0 019.5 1 3 3 0 01-.5 7z M11 14l-2 4h3l-2 4"/>', qty: '<path d="M4 6h16 M4 12h16 M4 18h10"/>',
};
const ico = k => `<svg class="i" viewBox="0 0 24 24">${RI[k] || RI.out}</svg>`;

/* a button that presses one of the editor's own controls (its disabled state followed), or runs a function */
function rbBtn(o) {
  const b = document.createElement("button");
  b.className = "rb-btn" + (o.big ? " big" : ""); b.type = "button"; b.title = o.title || o.label;
  if (o.id) b.id = o.id; b.dataset.testid = o.id || ("rb-" + o.label.toLowerCase().replace(/[^a-z0-9]+/g, "-"));
  const src = o.press && document.getElementById(o.press);
  const icon = o.icon ? ico(o.icon) : src && src.querySelector("svg") ? src.querySelector("svg").outerHTML : ico("out");
  b.innerHTML = `${icon}<span>${esc(o.label)}</span>`;
  b.addEventListener("click", e => { e.stopPropagation(); rbPeekEnd(); if (o.run) o.run(); else if (src) src.click(); });
  if (src) { const sync = () => { b.disabled = src.disabled; b.classList.toggle("on", src.classList.contains("active") || src.classList.contains("on") && o.toggle); }; sync(); new MutationObserver(sync).observe(src, { attributes: true, attributeFilter: ["disabled", "class"] }); }
  if (o.on) { b._on = o.on; rbBtn.toggles.push(b); }
  return b;
}
rbBtn.toggles = [];
function rbSyncToggles() { for (const b of rbBtn.toggles) b.classList.toggle("on", !!b._on()); }
/* a labelled field holding one of the editor's own controls, moved here (handlers and ids travel with it) */
function rbField(label, el, cls) {
  const w = document.createElement("label"); w.className = "rb-field" + (cls ? " " + cls : "");
  if (label) { const s = document.createElement("span"); s.textContent = label; w.appendChild(s); }
  if (el) { el.hidden = false; w.appendChild(el); }
  return w;
}
function rbCheck(el) {                                         // a checkbox's own <label> moved as it is
  const l = el && el.closest("label"); if (!l) return document.createElement("span");
  l.classList.add("rb-chk"); return l;
}
function rbGroup(title, items, opts) {
  const g = document.createElement("div"); g.className = "rb-group" + (opts && opts.cls ? " " + opts.cls : "");
  const body = document.createElement("div"); body.className = "rb-items";
  for (const it of items) if (it) body.appendChild(it);
  const t = document.createElement("div"); t.className = "rb-gt"; t.textContent = title;
  g.append(body, t); return g;
}
const press = id => () => { const el = document.getElementById(id); if (el) el.click(); };
const needSel = (table, fn, msg) => () => { if (state.sel.table !== table || !state.sel.ids.length) { toast(msg, "info"); return; } fn(state.sel.ids.slice()); };
const panel = (tab, on) => () => { showTab(tab); if (ui.bottomCollapsed) setBottom(false); if (on) on(); };
function rbTool(t) { return document.getElementById("tool-" + t); }

/* ------------------------------------------------------------------ build */
function buildRibbon() {
  document.body.classList.add("ribbon");
  const R = document.createElement("div"); R.id = "ribbon";
  R.innerHTML = `<div id="rb-top"><div class="brand"><span class="logo"><svg class="i" viewBox="0 0 24 24" style="stroke:#fff"><path d="M4 16c3-6 5-6 8 0s5 6 8 0"/></svg></span>Sewer network editor</div>
    <div id="rb-qat"></div><div id="rb-tabs" role="tablist"></div><div class="sp"></div><div id="rb-right"></div>
    <button id="rb-collapse" class="rb-ico" title="Collapse the ribbon to its tabs (Ctrl+F1); double-click a tab does the same">${ico("up")}</button></div>
    <div id="rb-panel"></div>`;
  document.body.insertBefore(R, $("#status-bar"));
  const qat = $("#rb-qat", R), tabs = $("#rb-tabs", R), pnl = $("#rb-panel", R), right = $("#rb-right", R);
  for (const [id, ic, t] of [["save-btn", "save", "Save (download the project)"], ["undo-btn", "undo", "Undo (Ctrl+Z)"], ["redo-btn", "redo", "Redo (Ctrl+Y)"]]) {
    const b = rbBtn({ press: id, icon: ic, label: "", title: t, id: "qat-" + id }); b.classList.add("rb-ico"); qat.appendChild(b);
  }
  right.append($("#find-wrap"), rbBtn({ press: "theme-btn", icon: "theme", label: "", title: "Light or dark theme", id: "rb-theme" }));
  right.lastChild.classList.add("rb-ico");

  const PAGES = [
    ["file", "File", () => [
      rbGroup("Project", [rbBtn({ press: "new-btn", icon: "new", label: "New", big: true }), rbBtn({ press: "open-btn", icon: "open", label: "Open .gpkg", big: true }),
        rbBtn({ press: "sample-btn", icon: "sample", label: "Sample", big: true }), rbBtn({ press: "save-btn", icon: "save", label: "Save", big: true })]),
      rbGroup("SewerGEMS", [rbBtn({ press: "sg-btn", icon: "sg", label: "Open SewerGEMS model", big: true })]),
      rbGroup("Import", [rbBtn({ press: "import-btn", icon: "imp", label: "EPA SWMM .inp" }), rbBtn({ press: "gis-btn", icon: "imp", label: "GIS layers" })]),
      rbGroup("Export", [rbBtn({ press: "export-btn", icon: "exp", label: "EPA SWMM .inp" }), rbBtn({ press: "export-dxf-btn", icon: "exp", label: "DXF" }),
        rbBtn({ press: "export-csv-btn", icon: "exp", label: "CSV" }), rbBtn({ press: "export-kmz-btn", icon: "exp", label: "KMZ (as the map)" })]),
    ]],
    ["home", "Home", () => [
      rbGroup("Scenario", [rbField("Active", $("#scenario-select"), "wide"), rbBtn({ press: "copy-btn", icon: "copy", label: "Copy" }), rbBtn({ press: "scen-btn", icon: "scen", label: "Scenarios..." }),
        rbBtn({ icon: "layers", label: "Alternatives...", title: "Named sets of loads, pumps, settings... shared by the scenarios that take them", run: () => openAlternatives() })]),
      rbGroup("Edit", [rbBtn({ press: "undo-btn", icon: "undo", label: "Undo" }), rbBtn({ press: "redo-btn", icon: "redo", label: "Redo" }),
        rbBtn({ icon: "del", label: "Delete", title: "Delete the selection (Del)", run: () => { if (!state.sel.ids.length && !state.mix) { toast("Select something first.", "info"); return; } if (typeof deleteSelection === "function") { deleteSelection(); return; } const t = state.sel.table, ids = state.sel.ids.slice(); enqueue(() => deleteIds(t, ids)); } }),
        rbBtn({ icon: "find", label: "Find", title: "Find an element by its ID (Ctrl+F)", run: () => { $("#find-input").focus(); $("#find-input").select(); } })]),
      rbGroup("Select", [rbBtn({ press: "tool-select", label: "Select", big: true }), rbBtn({ press: "tool-box", label: "Box" }), rbBtn({ press: "tool-poly", label: "Polygon" }),
        rbField("Selects", $("#sel-target")),
        rbBtn({ icon: "tbl", label: "By type...", title: "All pipes, conduits, pumps, structures of a kind, catchments", run: () => { const r = $("#rb-page-home").getBoundingClientRect(); selectMenu(260, r.bottom + 2); } }),
        rbBtn({ icon: "rev", label: "Invert", title: "Invert the selection", run: () => state.model && invertSelection() }),
        rbBtn({ icon: "layers", label: "Sets...", title: "Selection sets kept with the project (Ctrl+3)", run: () => { const r = $("#rb-page-home").getBoundingClientRect(); state.model && selSetMenu(420, r.bottom + 2); } }),
        rbBtn({ icon: "find", label: "Query...", title: "Select by a field: diameter, slope, velocity... (Ctrl+5)", run: () => openQuery() }),
        rbBtn({ icon: "del", label: "Clear", title: "Clear the selection (Esc)", run: () => setSel(null, []) })], { cls: "rb-form" }),
      rbGroup("Network navigator", [rbBtn({ icon: "layers", label: "Connected", title: "Everything connected to the selected structure or pipe", run: () => state.model && findConnected() }),
        rbBtn({ icon: "up", label: "Upstream", title: "Trace upstream of the selection (U)", run: () => state.sel.ids.length ? trace("up") : toast("Select a node or pipe first.", "info") }),
        rbBtn({ icon: "down", label: "Downstream", title: "Trace downstream of the selection (D)", run: () => state.sel.ids.length ? trace("down") : toast("Select a node or pipe first.", "info") }),
        rbBtn({ icon: "prof", label: "Path between", title: "The shortest path between two selected structures", run: () => state.model && findPath() }),
        rbBtn({ icon: "find", label: "Find...", title: "Isolated structures, two leaving pipes, ends that are not outfalls, pipes that reach no outfall, failing pipes, coincident structures",
          run: () => { const r = $("#rb-page-home").getBoundingClientRect(); navMenu(560, r.bottom + 2); } })]),
      rbGroup("Calculate", [rbBtn({ icon: "design", label: "Design...", big: true, title: "Size every conduit and lay it (scope, preview, then apply)", run: () => openDesignDlg() }),
        rbBtn({ icon: "check", label: "Checks", title: "The failing links", run: () => runNamed("checks") }), rbBtn({ icon: "storm", label: "Run storm (SWMM)", title: "Rain, catchments and dynamic routing on EPA SWMM 5", run: () => runNamed("storm") })]),
      rbGroup("Panels", [rbBtn({ press: "props-btn", icon: "props", label: "Properties", toggle: true }), rbBtn({ press: "bottom-btn", icon: "bottom", label: "Tables", toggle: true }), rbBtn({ press: "maxmap-btn", icon: "max", label: "Map only", toggle: true })]),
    ]],
    ["layout", "Layout", () => [
      rbGroup("Select", [rbBtn({ press: "tool-select", label: "Select", big: true }), rbBtn({ press: "tool-box", label: "Box" }), rbBtn({ press: "tool-poly", label: "Polygon" }),
        rbBtn({ press: "tool-move", label: "Move" }), rbBtn({ press: "tool-delete", label: "Delete" })]),
      rbGroup("Draw", [rbBtn({ press: "tool-layout", label: "Layout", big: true })]),
      // every element SewerGEMS draws (v7, 2026-11-24): structures, then links, then areas
      rbGroup("Structures", [rbBtn({ press: "tool-manhole", label: "Manhole" }), rbBtn({ press: "tool-catchbasin", label: "Catch basin" }), rbBtn({ press: "tool-outfall", label: "Outfall" }),
        rbBtn({ press: "tool-headwall", label: "Headwall" }), rbBtn({ press: "tool-transition", label: "Transition" }), rbBtn({ press: "tool-xsection", label: "Cross section" }),
        rbBtn({ press: "tool-wetwell", label: "Wet well" }), rbBtn({ press: "tool-pond", label: "Pond" }), rbBtn({ press: "tool-pjunction", label: "Pr. junction" }),
        rbBtn({ press: "tool-airvalve", label: "Air valve" }), rbBtn({ press: "tool-propconn", label: "Property" }), rbBtn({ press: "tool-tap", label: "Tap" })]),
      rbGroup("Links", [rbBtn({ press: "tool-pipe", label: "Conduit" }), rbBtn({ press: "tool-channel", label: "Channel" }), rbBtn({ press: "tool-gutter", label: "Gutter" }),
        rbBtn({ press: "tool-lateral", label: "Lateral" }), rbBtn({ press: "tool-pump", label: "Pump" }), rbBtn({ press: "tool-ppipe", label: "Force main" }),
        rbBtn({ press: "tool-orifice", label: "Orifice" }), rbBtn({ press: "tool-weir", label: "Weir" })]),
      rbGroup("Areas", [rbBtn({ press: "tool-catchment", label: "Catchment" })]),
      rbGroup("Layout run", [rbField("Structure", $("#layout-node")), rbField("Link", $("#layout-link")), rbField("Manholes", $("#layout-spacing"), "wide"), rbField("Max (m)", $("#layout-custom")), rbField("", $("#layout-note"), "note")], { cls: "rb-form" }),
      rbGroup("Modify", [
        rbBtn({ icon: "rev", label: "Reverse", title: "Turn the selected pipes round", run: needSel("links", ids => enqueue(() => exec({ op: "reverse", ids })), "Select the pipes to reverse.") }),
        rbBtn({ icon: "recon", label: "Reconnect", title: "Move the stop of the selected pipe to another node (right-click a pipe for the start)", run: needSel("links", ids => startReconnect(ids[0], "to"), "Select the pipe to reconnect.") }),
        rbBtn({ icon: "morph", label: "Morph...", title: "Change the selected structures to another kind (or click one with a structure tool)", run: needSel("nodes", ids => morphPick(ids), "Select the structures to change.") }),
        rbBtn({ press: "tool-measure", label: "Measure" })]),
      rbGroup("Prototypes", [rbBtn({ icon: "proto", label: "Prototypes...", big: true, title: "What a new element gets", run: () => openPrototypes() })]),
    ]],
    ["components", "Components", () => [
      rbGroup("Defaults", [rbBtn({ icon: "proto", label: "Prototypes...", big: true, run: () => openPrototypes() }), rbBtn({ icon: "lib", label: "Engineering libraries...", big: true, run: () => openLibraries() })]),
      rbGroup("Pumps", [rbBtn({ icon: "run", label: "Pump definitions...", big: true, title: "Pump curves (design point, three points, table) and the force mains' friction, with each pump's system curve",
        run: () => openPumpDefs(state.sel.table === "links" && state.sel.ids.length === 1 && state.model.links.get(state.sel.ids[0]) && state.model.links.get(state.sel.ids[0]).properties.kind === "pump" ? state.sel.ids[0] : null) })]),
      rbGroup("Sanitary", [rbBtn({ icon: "load", label: "Unit loads...", title: "Unit sanitary loads: population, area, discharge, count", run: () => openUnitLoads() }),
        rbBtn({ icon: "hydro", label: "Patterns...", title: "Hourly patterns and the dry-weather flow in SWMM runs", run: () => openPatterns() })]),
      rbGroup("Loads", [rbBtn({ icon: "tbl", label: "Loads table", title: "The Nodes table: each structure's unit load (peaked) and sanitary load (not peaked); paste columns from Excel", run: panel("nodes") }),
        rbBtn({ icon: "peak", label: "Peaking", title: "The peaking method and table (Settings)", run: panel("settings", () => scrollSet("set-peaking.method")) }),
        rbBtn({ icon: "infil", label: "Infiltration", title: "The infiltration method and rate (Settings); a pipe's own rate in its Properties", run: panel("settings", () => scrollSet("set-infiltration.method")) })]),
      rbGroup("Storm", [rbBtn({ icon: "rain", label: "Rain", title: "The rain (Settings)", run: panel("settings", () => scrollSet("rain-box")) }),
        rbBtn({ icon: "run", label: "Controls...", title: "Control rules for pumps, orifices and weirs in the storm run", run: () => openControls() })]),
      rbGroup("Units", [rbBtn({ icon: "units", label: "Units...", big: true, title: "Flows, loads and infiltration units", run: () => openUnits() })]),
    ]],
    ["analysis", "Analysis", () => [
      rbGroup("Validate", [rbBtn({ icon: "check", label: "Validate", big: true, title: "User notifications: errors and warnings (F8)", run: () => enqueue(runValidate) })]),
      rbGroup("Calculate", [rbBtn({ icon: "design", label: "Design...", big: true, run: () => openDesignDlg() }), rbBtn({ icon: "check", label: "Checks", run: () => runNamed("checks") }),
        rbBtn({ icon: "storm", label: "Run storm (SWMM)", run: () => runNamed("storm") }), rbBtn({ icon: "qty", label: "Quantities", run: () => runNamed("quantities") })]),
      rbGroup("Results", [rbField("Shown", $("#results-source"), "wide")], { cls: "rb-form" }),
      rbGroup("Design", [rbBtn({ icon: "design", label: "Design constraints", big: true, title: "Velocity, cover, d/D and minimum gradient by size, the pipe catalogues", run: () => openSettingsGroup("Design constraints") })]),
      rbGroup("Options", [rbBtn({ icon: "props", label: "Calculation options", big: true, title: "Named sets of options, saved and applied per scenario; the options themselves in Settings",
        run: () => { if (!state.model) return; const r = $("#rb-page-analysis").getBoundingClientRect(); calcMenu(r.left + 420, r.bottom + 2); } }),
        rbBtn({ icon: "scen", label: "Batch run...", title: "The steady run of several scenarios side by side", run: () => openBatch() })]),
      rbGroup("Storm (steady)", [rbBtn({ icon: "storm", label: "Rational method", title: "Q = C i A / 360 with the catchments' C and Tc and the IDF table", run: () => enqueue(runRational) }),
        rbBtn({ icon: "storm", label: "Design inlets", title: "Size each catalogue inlet marked Design inlet opening: the shortest of its design lengths that meets its minimum efficiency on grade, or its maximum depth and spread in a sag (undo takes it back)", run: () => enqueue(designInlets) })]),
      rbGroup("SewerGEMS", [rbBtn({ press: "sg-btn", icon: "sg", label: "Open model..." }), rbBtn({ icon: "check", label: "Compare (stored)", title: "Compare with the results SewerGEMS stored", run: () => runNamed("compare_stored") })]),
    ]],
    ["report", "Report", () => [
      rbGroup("Tables", [rbBtn({ icon: "tbl", label: "Nodes", run: panel("nodes") }), rbBtn({ icon: "tbl", label: "Links", run: panel("links") }), rbBtn({ icon: "tbl", label: "Results", run: panel("results") })]),
      rbGroup("Views", [rbBtn({ icon: "prof", label: "Profile", big: true, run: panel("profile") }), rbBtn({ icon: "sum", label: "Summary", run: panel("summary") }),
        rbBtn({ icon: "check", label: "Notifications", run: () => enqueue(runValidate) }),
        rbBtn({ icon: "hydro", label: "Hydrograph", run: panel("hydro") }), rbBtn({ icon: "out", label: "Tool output", run: panel("toolout") })]),
      rbGroup("Export", [rbBtn({ press: "export-csv-btn", icon: "exp", label: "CSV" }), rbBtn({ press: "export-dxf-btn", icon: "exp", label: "DXF" }), rbBtn({ press: "export-kmz-btn", icon: "exp", label: "KMZ" })]),
    ]],
    ["view", "View", () => [
      rbGroup("Symbology", [rbField("Pipes by", $("#color-by")), rbField("Structures by", $("#node-color-by")), rbField("Catchments by", $("#catch-color-by")),
        rbField("Set", $("#sym-def")), rbBtn({ icon: "sym", label: "Element Symbology", title: "The Element Symbology pane on the left (Ctrl+1)", on: () => document.body.classList.contains("sym-docked"), run: () => state.model && symDock(!document.body.classList.contains("sym-docked")) })], { cls: "rb-form" }),
      rbGroup("On the map", [rbCheck($("#arrows-toggle")), rbCheck($("#fail-toggle")), rbBtn({ icon: "legend", label: "Legend", title: "Show or hide the legend", on: () => !ui.legendHidden, run: () => { ui.legendHidden = !ui.legendHidden; saveUi(); rbLegend(); } })], { cls: "rb-form" }),
      rbGroup("Basemap", [rbField("Map", $("#basemap-select")), rbField("Opacity", $("#basemap-opacity")), rbCheck($("#labels-toggle")), rbCheck($("#hillshade-toggle"))], { cls: "rb-form" }),
      rbGroup("Layers", [rbBtn({ icon: "layers", label: "Reference layers...", big: true, title: "Plots, roads, a survey DXF under the network", run: () => rbPop("refs") })]),
      rbGroup("Zoom", [rbBtn({ icon: "fit", label: "Fit all", title: "The whole network (H)", run: () => fitModel() }), rbBtn({ icon: "zsel", label: "Selection", title: "Zoom to the selection (Z)", run: () => state.sel.ids.length && zoomTo(state.sel.table, state.sel.ids) })]),
      rbGroup("Panels", [rbBtn({ press: "props-btn", icon: "props", label: "Properties", toggle: true }), rbBtn({ press: "bottom-btn", icon: "bottom", label: "Tables", toggle: true }),
        rbBtn({ press: "maxmap-btn", icon: "max", label: "Map only", toggle: true }), rbBtn({ press: "theme-btn", icon: "theme", label: "Theme" })]),
    ]],
    ["tools", "Tools", () => [rbGroup("Builders", [rbBtn({ icon: "load", label: "LoadBuilder...", big: true, title: "Loads from a GIS layer to the nearest structures", run: () => openLoadBuilder() }),
        rbBtn({ icon: "imp", label: "TRex...", big: true, title: "Ground levels from a terrain GeoTIFF", run: () => openTRex() })]), rbGroup("Tools", [], { cls: "rb-tools" }), rbGroup("Assistant", [rbBtn({ icon: "asst", label: "Design assistant", big: true, run: panel("assistant") })])]],
    ["help", "Help", () => [
      rbGroup("Help", [rbBtn({ press: "keys-btn", icon: "keys", label: "Keyboard and mouse", big: true })]),
      rbGroup("Interface", [rbBtn({ icon: "classic", label: "Classic toolbar", big: true, title: "The same editor with the earlier toolbar", run: () => { location.href = "/"; } })]),
    ]],
  ];
  for (const [key, title, make] of PAGES) {
    const t = document.createElement("button"); t.className = "rb-tab"; t.textContent = title; t.dataset.tab = key; t.id = "rb-tab-" + key; t.setAttribute("role", "tab"); tabs.appendChild(t);
    const p = document.createElement("div"); p.className = "rb-page"; p.dataset.tab = key; p.id = "rb-page-" + key; p.hidden = true;
    for (const g of make()) p.appendChild(g);
    pnl.appendChild(p);
  }
  // the old chrome goes: its controls now live in the ribbon (the hidden elements stay for their handlers)
  $("#topbar").hidden = true; $("#tools").hidden = true;
  const legendHost = document.createElement("div"); legendHost.id = "legend-panel";
  legendHost.innerHTML = `<div class="lp-h" title="Fold or unfold the legend">Legend<button id="legend-close" title="Hide the legend (View > Legend)">&times;</button></div>`;
  legendHost.appendChild($("#legend")); $("#map-wrap").appendChild(legendHost);
  $("#display-card").hidden = true;
  legendHost.querySelector(".lp-h").addEventListener("click", e => { if (e.target.id === "legend-close") { ui.legendHidden = true; saveUi(); rbLegend(); return; } ui.legendFolded = !ui.legendFolded; saveUi(); rbLegend(); });
  // pop-overs for what does not fit a ribbon (reference layers)
  const pop = document.createElement("div"); pop.id = "rb-pop"; pop.hidden = true; document.body.appendChild(pop);
  pop.appendChild($(".refs")); pop.addEventListener("click", e => e.stopPropagation());
  // tabs: click selects; double-click (or the button, or Ctrl+F1) collapses; a click on a collapsed ribbon peeks
  tabs.addEventListener("click", e => { const t = e.target.closest(".rb-tab"); if (!t) return; e.stopPropagation(); rbShow(t.dataset.tab, true); });
  tabs.addEventListener("dblclick", e => { if (e.target.closest(".rb-tab")) rbCollapse(!ui.ribbonCollapsed); });
  $("#rb-collapse").addEventListener("click", e => { e.stopPropagation(); rbCollapse(!ui.ribbonCollapsed); });
  document.addEventListener("keydown", e => { if (e.ctrlKey && e.key === "F1") { e.preventDefault(); rbCollapse(!ui.ribbonCollapsed); } });
  document.addEventListener("click", e => { if (!e.target.closest("#rb-pop")) $("#rb-pop").hidden = true; if (!e.target.closest("#ribbon")) rbPeekEnd(); });
  // the Tools page follows the server's tool register (as the old Tools menu did)
  new MutationObserver(rbTools).observe($("#tools-menu"), { childList: true }); rbTools();
  rbShow(ui.ribbonTab || "home", false); rbCollapse(!!ui.ribbonCollapsed); rbLegend();
  setInterval(rbSyncToggles, 700);
}
function rbShow(key, user) {
  ui.ribbonTab = key; saveUi();
  $$(".rb-tab").forEach(t => t.classList.toggle("on", t.dataset.tab === key));
  $$(".rb-page").forEach(p => { p.hidden = p.dataset.tab !== key; });
  if (ui.ribbonCollapsed && user) $("#ribbon").classList.add("peek");
  if (key === "layout" && layoutCard.sync) layoutCard.sync();
  rbSyncToggles();
}
function rbPeekEnd() { const r = $("#ribbon"); if (r) r.classList.remove("peek"); }
function rbCollapse(on) {
  ui.ribbonCollapsed = on; saveUi();
  $("#ribbon").classList.toggle("collapsed", on); rbPeekEnd();
  $("#rb-collapse").innerHTML = ico(on ? "down" : "up"); $("#rb-collapse").title = on ? "Pin the ribbon open (Ctrl+F1)" : "Collapse the ribbon to its tabs (Ctrl+F1); double-click a tab does the same";
  setTimeout(() => map.resize(), 0);
}
function rbLegend() {
  const p = $("#legend-panel"); if (!p) return;
  p.hidden = !!ui.legendHidden; p.classList.toggle("folded", !!ui.legendFolded); rbSyncToggles();
}
function rbPop(what) {
  const p = $("#rb-pop"); p.hidden = false;
  const b = $("#rb-page-view").getBoundingClientRect(); p.style.top = (b.bottom + 4) + "px"; p.style.left = "260px";
}
function rbTools() {
  const host = $(".rb-tools .rb-items"); if (!host) return; host.innerHTML = "";
  for (const b of $$("#tools-menu button[data-tool]")) host.appendChild(rbBtn({ icon: "run", label: b.textContent.trim(), title: b.title, run: () => b.click(), id: "rb-tool-" + b.dataset.tool }));
  if (!host.children.length) host.innerHTML = `<span class="muted small">Open a project.</span>`;
}
function scrollSet(id) { setTimeout(() => { const el = document.getElementById(id); if (el && typeof revealSetting === "function") revealSetting(el); if (el) { el.scrollIntoView({ block: "center" }); el.focus && el.focus(); } }, 60); }
function runNamed(name) {
  if (!state.pid) { toast("Open a project first.", "info"); return; }
  const b = $(`#tools-menu button[data-tool="${name}"]`); if (b) { b.click(); return; }
  toast(name === "compare_stored" ? "This model holds no SewerGEMS results to compare with." : "That tool is not available.", "info");
}
function morphPick(ids) {
  const kinds = state.info.node_kinds;
  ctxOpen(innerWidth / 2 - 80, 150, [{ head: `Change ${ids.length > 1 ? ids.length + " structures" : ids[0]} to` }, ...kinds.map(k => ({ label: (typeof KINDS !== "undefined" && KINDS[k]) ? KINDS[k][1] : k, key: "morph-" + k,
    run: () => enqueue(async () => { await exec({ op: "set", table: "nodes", ids, field: "kind", value: k }); toast(`Changed to ${k} (Ctrl+Z undoes).`, "info"); }) }))]);
}

if (RIBBON) { buildRibbon(); tag(); }
window.ed.ribbon = RIBBON;
