"use strict";
/* W19 v2 (2026-11-23, user trial F1-F6, F3): the right-click menu on the map, the layout tool's options, prototypes and
   engineering libraries. Loaded after editor.js and using its functions (setTool, exec, setSel, trace, ...). */

/* ------------------------------------------------------------------ right-click menu (F6 and the rest of SewerGEMS's) */
function ctxClose() { const m = $("#ctx-menu"); if (m) m.hidden = true; }
function ctxOpen(x, y, items) {
  let m = $("#ctx-menu");
  if (!m) { m = document.createElement("div"); m.id = "ctx-menu"; m.setAttribute("role", "menu"); document.body.appendChild(m); }
  m.innerHTML = items.map((it, i) => it === "-" ? `<hr>` : it.head ? `<div class="mh">${esc(it.head)}</div>` :
    `<button data-i="${i}" role="menuitem" data-testid="ctx-${esc(it.key || it.label.toLowerCase().replace(/[^a-z0-9]+/g, "-"))}"${it.disabled ? " disabled" : ""} title="${esc(it.title || "")}">${esc(it.label)}${it.keys ? `<span class="k">${esc(it.keys)}</span>` : ""}</button>`).join("");
  m.hidden = false;
  const r = m.getBoundingClientRect();
  m.style.left = Math.min(x, innerWidth - r.width - 6) + "px"; m.style.top = Math.min(y, innerHeight - r.height - 6) + "px";
  m.onclick = e => { const b = e.target.closest("button[data-i]"); if (!b) return; ctxClose(); items[+b.dataset.i].run(); };
}
function profileFrom(id) { $("#prof-start").value = id; $("#prof-via").value = ""; $("#prof-end").value = ""; showTab("profile"); if (ui.bottomCollapsed) setBottom(false); enqueue(() => drawProfile()); }
function ctxForPoint(e) {
  if (!state.pid || !state.model) return;
  const pt = e.point, ll = e.lngLat;
  if (state.tool === "layout" && layout.last) { layout.last = null; $("#hint").textContent = HINTS.layout; return; }   // ends the run, as SewerGEMS
  if (state.reconnect) { state.reconnect = null; $("#hint").textContent = HINTS[state.tool] || ""; return; }
  if (state.pipeStart) { state.pipeStart = null; highlight(); $("#hint").textContent = HINTS[state.tool] || ""; return; }
  const nn = nearestNode(pt, 12), nl = nn ? null : nearestLink(pt, 8), cm = nn || nl ? null : catchAt(ll);
  const items = [], X = e.originalEvent.clientX, Y = e.originalEvent.clientY;
  const inSel = (t, id) => state.sel.table === t && state.sel.ids.includes(id) && state.sel.ids.length > 1;
  if (nn) {
    const f = state.model.nodes.get(nn.id), kind = f.properties.kind, ids = inSel("nodes", nn.id) ? state.sel.ids.slice() : [nn.id];
    if (!inSel("nodes", nn.id)) setSel("nodes", [nn.id]);
    items.push({ head: ids.length > 1 ? `${ids.length} nodes` : `${kind} ${nn.id}` },
      { label: "Properties", keys: "F2", run: () => { setProps(false); } },
      { label: "Zoom to", keys: "Z", run: () => zoomTo("nodes", ids) },
      "-",
      { label: "Trace upstream", keys: "U", run: () => trace("up") }, { label: "Trace downstream", keys: "D", run: () => trace("down") },
      { label: "Find connected", key: "find-connected", run: findConnected },
      { label: "Long section from here", run: () => profileFrom(nn.id) },
      { label: "Start a layout run here", key: "layout-from", run: () => { setTool("layout"); layout.last = nn.id; setSel("nodes", [nn.id]); $("#hint").textContent = "Click the next point; Esc or right-click ends the run."; } },
      "-", { head: "Morph to" });
    for (const k of state.info.node_kinds) if (k !== kind)
      items.push({ label: k[0].toUpperCase() + k.slice(1), key: "morph-" + k, title: "Keeps the id, the position, the levels and the pipes", run: () => enqueue(async () => { await exec({ op: "set", table: "nodes", ids, field: "kind", value: k }); toast(`${ids.length > 1 ? ids.length + " nodes" : ids[0]} changed to ${k} (Ctrl+Z undoes).`, "info"); }) });
    items.push("-", { label: "Delete", keys: "Del", run: () => enqueue(() => deleteIds("nodes", ids)) });
  } else if (nl) {
    const f = state.model.links.get(nl.id), ids = inSel("links", nl.id) ? state.sel.ids.slice() : [nl.id];
    if (!inSel("links", nl.id)) setSel("links", [nl.id]);
    const p = f.properties;
    items.push({ head: ids.length > 1 ? `${ids.length} links` : `${p.kind} ${nl.id} (${p.from_node} to ${p.to_node})` },
      { label: "Properties", keys: "F2", run: () => setProps(false) },
      { label: "Zoom to", keys: "Z", run: () => zoomTo("links", ids) },
      "-",
      { label: "Trace upstream", keys: "U", run: () => trace("up") }, { label: "Trace downstream", keys: "D", run: () => trace("down") },
      { label: "Find connected", key: "find-connected", run: findConnected },
      { label: "Long section from here", run: () => profileFrom(nl.id) },
      "-",
      { label: "Reconnect start...", key: "reconnect-from", disabled: ids.length > 1, title: "Click the node the start should move to", run: () => startReconnect(nl.id, "from") },
      { label: "Reconnect stop...", key: "reconnect-to", disabled: ids.length > 1, title: "Click the node the stop should move to", run: () => startReconnect(nl.id, "to") },
      { label: "Reverse direction", key: "reverse", run: () => enqueue(() => exec({ op: "reverse", ids })) },
      { label: "Split here (insert a manhole)", key: "split", disabled: ids.length > 1, run: () => enqueue(async () => { await exec({ op: "split_link", id: nl.id, lon: ll.lng, lat: ll.lat }); }) },
      "-", { label: "Delete", keys: "Del", run: () => enqueue(() => deleteIds("links", ids)) });
  } else if (cm) {
    setSel("catchments", [cm]);
    items.push({ head: `catchment ${cm}` }, { label: "Properties", run: () => setProps(false) }, { label: "Zoom to", run: () => zoomTo("catchments", [cm]) },
      "-", { label: "Delete", run: () => enqueue(() => deleteIds("catchments", [cm])) });
  } else {
    items.push({ head: "Map" },
      { label: "Add a manhole here", key: "add-manhole", run: () => enqueue(async () => { const id = newId("nodes", "MH-"); await exec({ op: "add_node", id, kind: "manhole", lon: ll.lng, lat: ll.lat }); setSel("nodes", [id]); }) },
      { label: "Start a layout run here", key: "layout-here", run: () => { setTool("layout"); enqueue(() => act(ll, {})); } },
      { label: "Select by type...", key: "select-by-type", run: () => setTimeout(() => selectMenu(X, Y), 0) },
      { label: "Network navigator...", key: "navigator", run: () => setTimeout(() => navMenu(X, Y), 0) },
      "-", { label: "Fit the whole network", keys: "H", run: fitModel },
      { label: "Select", keys: "S", run: () => setTool("select") });
  }
  ctxOpen(X, Y, items);
}
function startReconnect(id, end) {
  state.reconnect = { id, end };
  $("#hint").textContent = `Reconnect ${id}: click the node its ${end === "from" ? "start" : "stop"} should move to (Esc cancels).`;
}

/* ------------------------------------------------------------------ the layout tool's options */
function layoutCard() {
  const c = document.createElement("div"); c.id = "layout-card"; c.hidden = true;
  c.innerHTML = `<div class="lc-h">Layout</div>
    <label for="layout-node">Structure</label><select id="layout-node" title="What each click places (its levels from the prototype)"><option value="manhole">Manhole</option><option value="outfall">Outfall</option><option value="wetwell">Wet well</option></select>
    <label for="layout-spacing">Manholes</label><select id="layout-spacing" title="Manholes put in between two clicks so no pipe is longer than this (the engineer's rounded spacing, 2026-08-18)">
      <option value="table12">at G203 Table 12 spacing (by size)</option><option value="custom">at most every...</option><option value="none">none: one pipe per click</option></select>
    <label for="layout-custom" id="layout-custom-l">Max spacing (m)</label><input id="layout-custom" type="number" min="5" step="any" value="100">
    <div class="muted small" id="layout-note"></div>`;
  $("#map-wrap").appendChild(c);
  const sync = () => {
    layout.node = $("#layout-node").value; layout.spacing = $("#layout-spacing").value; layout.custom = Number($("#layout-custom").value) || 100;
    const cu = layout.spacing === "custom"; $("#layout-custom").hidden = !cu; $("#layout-custom-l").hidden = !cu;
    const dn = (state.model && state.model.settings.prototypes && state.model.settings.prototypes.conduit && state.model.settings.prototypes.conduit.dn_mm) || (state.info && state.info.catalogue[0]) || 200;
    $("#layout-note").textContent = layout.spacing === "table12" ? `DN${dn}: ${dn <= 315 ? 100 : dn <= 900 ? 120 : dn <= 1400 ? 150 : 200} m maximum (p30); 230 m gives 80 + 80 + 70.` : layout.spacing === "custom" ? "Rounded to 10 m pieces, never over the maximum." : "";
    try { localStorage.setItem("w19.layout", JSON.stringify({ node: layout.node, spacing: layout.spacing, custom: layout.custom })); } catch (e) { /* not kept */ }
  };
  try { const s = JSON.parse(localStorage.getItem("w19.layout") || "{}"); if (s.node) $("#layout-node").value = s.node; if (s.spacing) $("#layout-spacing").value = s.spacing; if (s.custom) $("#layout-custom").value = s.custom; } catch (e) { /* defaults */ }
  for (const id of ["layout-node", "layout-spacing", "layout-custom"]) $("#" + id).addEventListener("change", sync);
  sync(); layoutCard.sync = sync;
}

/* ------------------------------------------------------------------ prototypes and engineering libraries (F3) */
const PROTO_FIELDS = {
  manhole: [["ground", "Ground level", "m"], ["depth", "Depth (ground to invert)", "m"]],
  outfall: [["ground", "Ground level", "m"], ["depth", "Depth (ground to invert)", "m"]],
  wetwell: [["ground", "Ground level", "m"], ["depth", "Depth (ground to invert)", "m"]],
  catchment: [["imperv_pc", "Impervious", "%"], ["width_m", "Width (blank: from the area)", "m"], ["slope_pc", "Slope", "%"], ["n_imperv", "n impervious", ""], ["n_perv", "n pervious", ""]],
};
const PROTO_NAMES = { manhole: "Manhole", outfall: "Outfall", wetwell: "Wet well", conduit: "Conduit", catchment: "Catchment" };
function protoOf(kind) { const P = (state.model && state.model.settings.prototypes) || {}; return P[kind] || {}; }
function libSections() { return ((state.model && state.model.settings.libraries) || {}).sections || []; }
function dlg(id, title, wide) {
  let d = $("#" + id);
  if (!d) { d = document.createElement("div"); d.id = id; d.className = "modal"; d.hidden = true; d.innerHTML = `<div class="dlg ${wide ? "wide" : ""}"><h3></h3><div class="body"></div><div class="row"><button class="primary" data-act="ok">Apply</button><button data-act="close">Close</button></div></div>`; document.body.appendChild(d); }
  d.querySelector("h3").textContent = title; return d;
}
function openPrototypes() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-proto", "Prototypes: what a new element gets", true), b = d.querySelector(".body");
  const cat = state.info.catalogue, secs = libSections(), cp = protoOf("conduit");
  const cur = cp.section ? "sec:" + (secs.findIndex(s => JSON.stringify(s.section) === JSON.stringify(cp.section))) : String(cp.dn_mm || cat[0]);
  let h = `<p class="muted">Each new element drawn takes these values; change them on the element afterwards. Kept with the project (undo takes a change back).</p><div class="proto-grid">`;
  for (const [k, F] of Object.entries(PROTO_FIELDS)) {
    const p = protoOf(k);
    h += `<fieldset><legend>${PROTO_NAMES[k]}</legend>` + F.map(([f, l, u]) => `<label>${l}${u ? ` (${u})` : ""}<input type="number" step="any" data-k="${k}" data-f="${f}" data-testid="proto-${k}-${f}" value="${p[f] ?? ""}"></label>`).join("") + `</fieldset>`;
  }
  h += `<fieldset><legend>Conduit</legend><label>Size or section<select data-k="conduit" data-f="size" data-testid="proto-conduit-size">` +
    cat.map(n => `<option value="${n}"${String(n) === cur ? " selected" : ""}>DN${n} (catalogue)</option>`).join("") +
    secs.map((s, i) => `<option value="sec:${i}"${"sec:" + i === cur ? " selected" : ""}>${esc(s.name)} (library)</option>`).join("") + `</select></label></fieldset></div>`;
  b.innerHTML = h; d.hidden = false;
  d.onclick = e => {
    const a = e.target.dataset && e.target.dataset.act; if (!a) return;
    if (a === "close") { d.hidden = true; return; }
    const ops = [];
    for (const k of Object.keys(PROTO_FIELDS)) {
      const vals = {};
      for (const inp of $$(`input[data-k="${k}"]`, b)) { if (inp.value === "") continue; const v = Number(inp.value); if (!isFinite(v)) { toast(`${PROTO_NAMES[k]}: ${inp.dataset.f} is not a number.`); return; } vals[inp.dataset.f] = v; }
      ops.push({ op: "set_prototype", kind: k, values: vals });
    }
    const sv = $(`select[data-k="conduit"]`, b).value;
    ops.push({ op: "set_prototype", kind: "conduit", values: sv.startsWith("sec:") ? { dn_mm: null, section: secs[+sv.slice(4)].section } : { dn_mm: Number(sv), section: null } });
    d.hidden = true;
    enqueue(async () => { await exec({ op: "batch", ops }); await loadModel(); if (layoutCard.sync) layoutCard.sync(); toast("Prototypes applied: new elements take them (one undo step).", "info"); });
  };
}
function openLibraries() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-lib", "Engineering libraries", true), b = d.querySelector(".body");
  const draft = (d._draft = d._draft && d._pid === state.pid ? d._draft : libSections().map(s => JSON.parse(JSON.stringify(s)))); d._pid = state.pid;
  const shapes = SEC_SHAPES.filter(s => s[0] !== "circle");
  const render = () => {
    b.innerHTML = `<div class="tabs-mini" id="lib-tabs"><button class="on" data-t="sec">Cross-sections</button><button data-t="sizes">Conduit sizes</button><button data-t="more">Peaking, infiltration, rain</button></div>
      <div data-p="sec"><p class="muted">Named boxes and open channels, kept with the project. Apply one to the selected conduits, or make it the conduit prototype.</p>
      <table class="lib-tab"><thead><tr><th>Name</th><th>Shape</th><th>Span / bottom (m)</th><th>Rise (m)</th><th>Side slopes H:1V</th><th>n</th><th>Barrels</th><th></th></tr></thead><tbody>` +
      draft.map((s, i) => { const x = s.section; return `<tr data-i="${i}"><td><input data-f="name" value="${esc(s.name)}"></td><td><select data-f="shape">${shapes.map(([v, l]) => `<option value="${v}"${v === x.shape ? " selected" : ""}>${l}</option>`).join("")}</select></td>` +
        `<td><input type="number" step="any" data-f="${x.shape === "trapezoid" ? "bottom_m" : "span_m"}" value="${x.shape === "trapezoid" ? x.bottom_m ?? "" : x.span_m ?? ""}"></td><td><input type="number" step="any" data-f="rise_m" value="${x.rise_m ?? ""}"></td>` +
        `<td>${x.shape === "trapezoid" ? `<input type="number" step="any" data-f="z_left" value="${x.z_left ?? 1.5}" style="width:52px"><input type="number" step="any" data-f="z_right" value="${x.z_right ?? 1.5}" style="width:52px">` : ""}</td>` +
        `<td><input type="number" step="any" data-f="n" value="${x.n ?? ""}"></td><td><input type="number" step="1" min="1" data-f="barrels" value="${x.barrels ?? 1}"></td>` +
        `<td><button data-a="use" title="Apply to the selected conduits">Apply to selection</button><button data-a="del" title="Remove from the library">&times;</button></td></tr>`; }).join("") +
      `</tbody></table><div class="row"><button data-a="add">Add a section</button></div></div>
      <div data-p="sizes" hidden><p class="muted">The pipe catalogue (nominal and inside diameter) is the conduit size library: the design and the size lists use it.</p><div class="row"><button data-a="goto-cat">Edit the catalogue (Settings)</button></div></div>
      <div data-p="more" hidden><p class="muted">The peaking table and method, the infiltration method and rate, the rain and the units are in Settings.</p><div class="row"><button data-a="goto-set">Open Settings</button></div></div>`;
    tag(b);
  };
  render(); d.hidden = false;
  const collect = () => {
    for (const tr of $$("tr[data-i]", b)) {
      const s = draft[+tr.dataset.i], x = { shape: $("[data-f=shape]", tr).value };
      for (const inp of $$("input[data-f]", tr)) { if (inp.dataset.f === "name") s.name = inp.value.trim() || s.name; else if (inp.value !== "") x[inp.dataset.f] = Number(inp.value); }
      if (x.shape === "trapezoid") delete x.span_m; else { delete x.bottom_m; delete x.z_left; delete x.z_right; }
      if (x.barrels === 1) delete x.barrels; s.section = x;
    }
  };
  b.onchange = e => { if (e.target.dataset.f === "shape") { collect(); render(); } };
  d.onclick = e => {
    const t = e.target, act = t.dataset.act || t.dataset.a, tab = t.dataset.t;
    if (tab) { $$("#lib-tabs button", b).forEach(x => x.classList.toggle("on", x === t)); $$("[data-p]", b).forEach(p => { p.hidden = p.dataset.p !== tab; }); return; }
    if (!act) return;
    if (act === "close") { d.hidden = true; return; }
    if (act === "goto-cat" || act === "goto-set") { d.hidden = true; showTab("settings"); if (ui.bottomCollapsed) setBottom(false); setTimeout(() => { const el = $("#tbl-design-catalogue"); if (el && act === "goto-cat") el.scrollIntoView({ block: "start" }); }, 50); return; }
    collect();
    if (act === "add") { draft.push({ name: `Box ${draft.length + 1}`, section: { shape: "box", span_m: 2, rise_m: 1.5, n: 0.015 } }); render(); return; }
    const i = +t.closest("tr[data-i]")?.dataset.i;
    if (act === "del") { draft.splice(i, 1); render(); return; }
    if (act === "use") {
      const ids = state.sel.table === "links" ? state.sel.ids.filter(id => state.model.links.get(id) && state.model.links.get(id).properties.kind === "conduit") : [];
      if (!ids.length) { toast("Select the conduits first (on the map or in the Links table)."); return; }
      enqueue(() => exec({ op: "set_section", ids, section: draft[i].section })); return;
    }
    if (act === "ok") {
      const bad = draft.find(s => !(s.section.rise_m > 0 && s.section.n > 0));
      if (bad) { toast(`${bad.name}: a section needs a positive rise and n.`); return; }
      enqueue(async () => { await exec({ op: "set_setting", path: "libraries.sections", value: draft }); d._draft = null; toast(`Library: ${draft.length} section${draft.length === 1 ? "" : "s"} saved with the project.`, "info"); d.hidden = true; });
    }
  };
}
/* units in a small dialog (the same choices as Settings > Units) */
function openUnits() {
  const d = dlg("dlg-units", "Units"), b = d.querySelector(".body");
  b.innerHTML = Object.entries(UNIT_CHOICES).map(([q, c]) => `<label>${c.title}<select data-unit="${q}" data-testid="units-${q}">${Object.keys(c.opts).map(u => `<option${u === unitPick(q) ? " selected" : ""}>${u}</option>`).join("")}</select></label>`).join("") +
    `<p class="muted small">How values are shown and typed (tables, properties, settings); the model is unchanged. Kept in this browser.</p>`;
  d.querySelector("[data-act=ok]").textContent = "Apply"; d.hidden = false;
  d.onclick = e => {
    const a = e.target.dataset.act; if (!a) return; d.hidden = true; if (a !== "ok") return;
    ui.units = Object.assign({}, ui.units); for (const s of $$("[data-unit]", b)) ui.units[s.dataset.unit] = s.value;
    saveUi(); $("#settings-form").dataset.sig = ""; gridSig = ""; renderAll();
  };
}

/* ------------------------------------------------------------------ ponds and pumps for the storm run */
function stormBlock(table, fs) {
  if (fs.length !== 1) return "";
  const p = fs[0].properties;
  if (table === "nodes" && (p.kind === "storage" || p.kind === "wetwell")) {
    const s = p.storage || {}, rows = (s.curve || []).map(r => r.join(" ")).join("\n");
    return `<h5>Storage (storm run)</h5><p class="muted small">The plan area SWMM stores water over: one area, or a depth-area table (a pond's banks). Rain falls on it through a catchment drawn over it with this outlet.</p>` +
      `<div class="pr"><label for="st-area">Area (constant)</label><input type="number" step="any" min="0" id="st-area" value="${s.area_m2 ?? ""}" placeholder="${s.curve ? "table below" : "SWMM default"}"><span class="u">m2</span></div>` +
      `<div class="pr" style="align-items:start"><label for="st-curve">or depth-area<br><span class="muted small">depth area, a row a line</span></label><textarea id="st-curve" rows="4" style="width:100%;font:12px monospace">${esc(rows)}</textarea><span class="u">m, m2</span></div>` +
      `<div class="row"><button id="st-apply">Apply storage</button><button id="st-clear">Clear</button></div>`;
  }
  if (table === "links" && p.kind === "pump") {
    const u = p.pump || {}, fu = unitOf("q_ls").u, k = unitOf("q_ls").k;
    return `<h5>Pump (storm run)</h5><p class="muted small">Pumps its capacity while the depth at its inlet is between the start and stop depths (SWMM, constant-capacity curve).</p>` +
      `<div class="pr"><label for="pu-q">Capacity</label><input type="number" step="any" min="0" id="pu-q" value="${u.q_ls != null ? +(u.q_ls * k).toFixed(4) : ""}" placeholder="ideal: passes its inflow"><span class="u">${fu}</span></div>` +
      `<div class="pr"><label for="pu-on">Starts at depth</label><input type="number" step="any" min="0" id="pu-on" value="${u.on_m ?? ""}"><span class="u">m</span></div>` +
      `<div class="pr"><label for="pu-off">Stops at depth</label><input type="number" step="any" min="0" id="pu-off" value="${u.off_m ?? ""}"><span class="u">m</span></div>` +
      `<div class="row"><button id="pu-apply">Apply pump</button><button id="pu-clear">Clear</button></div>`;
  }
  return "";
}
function wireStormBlock(host) {
  const id = () => state.sel.ids[0];
  const sa = $("#st-apply", host);
  if (sa) {
    sa.onclick = () => {
      const txt = $("#st-curve", host).value.trim(), a = $("#st-area", host).value;
      if (txt) {
        const curve = txt.split(/\n+/).map(l => l.trim().split(/[\s,;]+/).map(Number)).filter(r => r.length >= 2 && r.every(isFinite)).map(r => r.slice(0, 2));
        if (curve.length < 2) { toast("Give two or more rows of depth and area."); return; }
        enqueue(() => exec({ op: "set_storage", ids: [id()], curve }));
      } else if (a !== "") enqueue(() => exec({ op: "set_storage", ids: [id()], area_m2: Number(a) }));
      else toast("Give an area or a depth-area table.");
    };
    $("#st-clear", host).onclick = () => enqueue(() => exec({ op: "set_storage", ids: [id()] }));
  }
  const pa = $("#pu-apply", host);
  if (pa) {
    pa.onclick = () => {
      const q = $("#pu-q", host).value; if (q === "") { toast("Give the pump's capacity."); return; }
      enqueue(() => exec({ op: "set_pump", ids: [id()], q_ls: Number(q) / unitOf("q_ls").k, on_m: Number($("#pu-on", host).value || 0), off_m: Number($("#pu-off", host).value || 0) }));
    };
    $("#pu-clear", host).onclick = () => enqueue(() => exec({ op: "set_pump", ids: [id()] }));
  }
}

/* ------------------------------------------------------------------ selection by type, invert (F11) */
const SEL_TYPES = [
  ["All pipes and pumps", "links", () => true], ["All conduits", "links", p => p.kind === "conduit"], ["All pumps", "links", p => p.kind === "pump"],
  ["All structures", "nodes", () => true], ["All manholes", "nodes", p => p.kind === "manhole"], ["All outfalls", "nodes", p => p.kind === "outfall"],
  ["All wet wells", "nodes", p => p.kind === "wetwell"], ["All storage", "nodes", p => p.kind === "storage"], ["All catchments", "catchments", () => true],
];
function selectByType(i) {
  const [label, t, ok] = SEL_TYPES[i], F = { nodes: state.model.nodeFeat, links: state.model.linkFeat, catchments: state.model.catchFeat }[t];
  const ids = F.filter(f => ok(f.properties)).map(f => String(f.id)); setSel(t, ids); toast(`${label.toLowerCase()}: ${ids.length} selected.`, "info");
}
function selectMenu(x, y) {
  if (!state.model) return;
  ctxOpen(x, y, [{ head: "Select" }, ...SEL_TYPES.map((s, i) => ({ label: s[0], key: "selall-" + i, run: () => selectByType(i) })), "-",
    { label: "Invert the selection", key: "sel-invert", run: invertSelection }, { label: "Clear the selection", keys: "Esc", key: "sel-clear", run: () => setSel(null, []) }]);
}
function invertSelection() {
  const t = state.sel.table || "links", F = { nodes: state.model.nodeFeat, links: state.model.linkFeat, catchments: state.model.catchFeat }[t];
  const cur = new Set(state.sel.ids); setSel(t, F.map(f => String(f.id)).filter(i => !cur.has(i)));
}

/* ------------------------------------------------------------------ network navigator (F12), as SewerGEMS's */
function graph() {
  const m = state.model, adj = new Map(), out = new Map();
  const add = (n, l, o) => { if (!adj.has(n)) adj.set(n, []); adj.get(n).push([l, o]); };
  for (const f of m.linkFeat) {
    const p = f.properties, id = String(f.id); add(p.from_node, id, p.to_node); add(p.to_node, id, p.from_node);
    if (!out.has(p.from_node)) out.set(p.from_node, []); out.get(p.from_node).push(f);
  }
  return { adj, out };
}
const navResult = (links, msg) => { if (!links.length) { toast(msg + ": none.", "info"); return; } setSel("links", links, { zoom: true }); toast(`${msg}: ${links.length} pipe${links.length > 1 ? "s" : ""}.`, "info"); };
const navNodes = (nodes, msg) => { if (!nodes.length) { toast(msg + ": none.", "info"); return; } setSel("nodes", nodes, { zoom: true }); toast(`${msg}: ${nodes.length} structure${nodes.length > 1 ? "s" : ""}.`, "info"); };
function startNode() {
  if (state.sel.table === "nodes" && state.sel.ids.length) return state.sel.ids[0];
  if (state.sel.table === "links" && state.sel.ids.length) return state.model.links.get(state.sel.ids[0]).properties.from_node;
  toast("Select a structure or a pipe first.", "info"); return null;
}
function findConnected() {
  const s = startNode(); if (s == null) return;
  const { adj } = graph(), seen = new Set([s]), links = new Set(), q = [s];
  while (q.length) { const n = q.shift(); for (const [l, o] of adj.get(n) || []) { links.add(l); if (!seen.has(o)) { seen.add(o); q.push(o); } } }
  const outs = [...seen].filter(n => (state.model.nodes.get(n) || { properties: {} }).properties.kind === "outfall");
  navResult([...links], `Connected to ${s} (${seen.size} structures, ${outs.length} outfall${outs.length === 1 ? "" : "s"}${outs.length ? ": " + outs.slice(0, 3).join(", ") : ""})`);
}
function findPath() {
  if (state.sel.table !== "nodes" || state.sel.ids.length !== 2) { toast("Select two structures (Ctrl+click the second), then Path between.", "info"); return; }
  const [a, b] = state.sel.ids, { adj } = graph(), L = id => +state.model.links.get(id).properties.length_m || 0;
  const dist = new Map([[a, 0]]), prev = new Map(), done = new Set();
  while (true) {                                                    // Dijkstra on pipe lengths, either direction
    let u = null, du = Infinity; for (const [n, d] of dist) if (!done.has(n) && d < du) { u = n; du = d; }
    if (u == null || u === b) break; done.add(u);
    for (const [l, o] of adj.get(u) || []) { const d = du + L(l); if (d < (dist.get(o) ?? Infinity)) { dist.set(o, d); prev.set(o, [u, l]); } }
  }
  if (!prev.has(b)) { toast(`${a} and ${b} are not connected.`, "info"); return; }
  const links = []; for (let n = b; n !== a; n = prev.get(n)[0]) links.unshift(prev.get(n)[1]);
  setSel("links", links, { zoom: true }); toast(`Path ${a} to ${b}: ${links.length} pipes, ${(dist.get(b) / 1000).toFixed(3)} km.`, "info");
}
const FINDS = [
  ["Isolated structures (no pipe)", "find-isolated", () => { const { adj } = graph(); navNodes(state.model.nodeFeat.map(f => String(f.id)).filter(n => !adj.has(n)), "Isolated structures"); }],
  ["Structures with two leaving pipes", "find-two-leaving", () => { const { out } = graph(); navNodes([...out].filter(([, ls]) => ls.length > 1).map(([n]) => n), "Two or more leaving pipes (a sewer network is a tree)"); }],
  ["Ends that are not outfalls", "find-open-ends", () => {
    const { adj, out } = graph();
    navNodes(state.model.nodeFeat.filter(f => adj.has(String(f.id)) && !out.has(String(f.id)) && !["outfall", "storage"].includes(f.properties.kind)).map(f => String(f.id)), "Network ends that are not outfalls");
  }],
  ["Pipes that reach no outfall", "find-no-outfall", () => {
    const { out } = graph(), m = state.model, bad = [];
    for (const f of m.linkFeat) {
      let n = f.properties.to_node, k = 0; const seen = new Set();
      while (out.has(n) && !seen.has(n) && k++ < 100000) { seen.add(n); n = out.get(n)[0].properties.to_node; }
      const end = m.nodes.get(n); if (!end || end.properties.kind !== "outfall") bad.push(String(f.id));
    }
    navResult(bad, "Pipes whose flow reaches no outfall");
  }],
  ["Failing pipes", "find-failing", () => { const R = srcLinks(); navResult(state.model.linkFeat.filter(f => { const r = R[f.id]; return r && (r.over_limit || r.over_vmax || r.surcharged || r.negative_slope); }).map(f => String(f.id)), "Failing pipes"); }],
  ["Coincident structures (within 0.1 m)", "find-coincident", () => {
    const k = 0.1 / 111319.49, cell = new Map(), hit = new Set();
    for (const f of state.model.nodeFeat) {
      const [x, y] = f.geometry.coordinates, key = Math.round(x / k) + "," + Math.round(y / k);
      if (cell.has(key)) { hit.add(cell.get(key)); hit.add(String(f.id)); } else cell.set(key, String(f.id));
    }
    navNodes([...hit], "Structures on top of one another");
  }],
];
function navMenu(x, y) {
  if (!state.model) return;
  ctxOpen(x, y, [{ head: "Network navigator" },
    { label: "Find connected", key: "nav-connected", run: findConnected }, { label: "Trace upstream", keys: "U", key: "nav-up", run: () => trace("up") },
    { label: "Trace downstream", keys: "D", key: "nav-down", run: () => trace("down") }, { label: "Path between two structures", key: "nav-path", run: findPath },
    "-", { head: "Find" }, ...FINDS.map(([l, k, run]) => ({ label: l, key: k, run }))]);
}
/* the selection card (classic toolbar): what the box and polygon tools select */
function selectCard() {
  const c = document.createElement("div"); c.id = "select-card"; c.hidden = true;
  c.innerHTML = `<div class="lc-h">Select</div><label for="sel-target">Selects</label><select id="sel-target" title="What the box and polygon tools select"><option value="links">pipes</option><option value="nodes">structures</option><option value="catchments">catchments</option></select>
    <div class="row2"><button id="sel-type" title="All of one kind">By type...</button><button id="sel-nav" title="Connected, upstream, downstream, path, problems">Navigator...</button></div>`;
  $("#map-wrap").appendChild(c);
  $("#sel-target").addEventListener("change", e => { selWhat.target = e.target.value; });
  $("#sel-type").addEventListener("click", e => { e.stopPropagation(); const r = e.target.getBoundingClientRect(); selectMenu(r.left, r.bottom + 4); });
  $("#sel-nav").addEventListener("click", e => { e.stopPropagation(); const r = e.target.getBoundingClientRect(); navMenu(r.left, r.bottom + 4); });
}

/* ------------------------------------------------------------------ wiring */
(function wireFeatures() {
  map.on("contextmenu", e => { e.originalEvent.preventDefault(); ctxForPoint(e); });
  document.addEventListener("click", e => { if (!e.target.closest("#ctx-menu")) ctxClose(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") ctxClose(); });
  map.on("movestart", ctxClose);
  layoutCard(); selectCard();
  const base = setTool;                                       // the layout and select cards show with their tools
  setTool = function (t) {
    base(t); const rb = document.body.classList.contains("ribbon");
    const c = $("#layout-card"); if (c) c.hidden = t !== "layout" || rb;
    const s = $("#select-card"); if (s) s.hidden = !["box", "poly", "select"].includes(t) || rb || !state.pid;
  };
  tag();
  window.ed.ctx = (lon, lat) => { const ll = { lng: lon, lat }; const p = map.project(ll); ctxForPoint({ point: p, lngLat: ll, originalEvent: { clientX: p.x + 60, clientY: p.y + 120, preventDefault() {} } }); };
})();
