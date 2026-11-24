"use strict";
/* W19 v6 (2026-11-24), the engineer's F30-F41, built as if others use the app:
   - selection: Shift adds, Ctrl removes (click, box, polygon); a New / Add / Remove switch for a phone; no 3D tilt;
   - the middle button pans in every tool (SewerGEMS); a selected structure is dragged to move it, or Move... then a tap;
   - pipe bends: add, remove, drag; the layout tool's right-click chooses the next point (a structure type, or a bend);
   - the left dock holds Element Symbology and Background Layers as tabs, widened by dragging its edge;
   - colour by subnetwork: by outfall, pumping station, lift, or every wet well;
   - a link per model (the address bar), recent models kept in this browser; Find also finds tools;
   - a SewerGEMS model picked on any device; tools that read this computer's files shown only on it. */

const ENV = { local: true, sewergems: null };
async function loadEnv() {
  try { Object.assign(ENV, await jget("/env")); } catch (e) { /* an older server: everything shown */ }
  document.body.classList.toggle("remote-ui", !ENV.local);
}
loadEnv();

/* ------------------------------------------------------------------ the map: flat, north up by the compass, middle-button pan */
(async function mapBehaviour() {
  await mapReady;
  map.dragRotate.disable(); map.keyboard.disableRotation();         // Ctrl+drag selects; a phone still turns the map with two fingers
  map.setMaxPitch(0); if (map.touchPitch) map.touchPitch.disable();   // no 3D tilt: a plan stays a plan
  const cv = map.getCanvasContainer(); let mid = null;
  cv.addEventListener("mousedown", e => { if (e.button === 1) { e.preventDefault(); mid = { x: e.clientX, y: e.clientY }; cv.style.cursor = "grabbing"; } });
  addEventListener("mousemove", e => { if (!mid) return; map.panBy([mid.x - e.clientX, mid.y - e.clientY], { animate: false }); mid = { x: e.clientX, y: e.clientY }; });
  addEventListener("mouseup", e => { if (mid && e.button === 1) { mid = null; cv.style.cursor = ""; } });
  cv.addEventListener("auxclick", e => { if (e.button === 1) e.preventDefault(); });
})();

/* ------------------------------------------------------------------ selection: new, add, remove */
state.selMode = "new";
let selOpNext = null, polyOp = null;
function selModeBar() {
  let b = $("#sel-mode");
  if (!b) {
    b = document.createElement("div"); b.id = "sel-mode"; b.setAttribute("role", "radiogroup");
    b.innerHTML = [["new", "New", "A click or a box replaces the selection"], ["add", "Add", "Adds to the selection (or hold Shift)"], ["remove", "Remove", "Takes out of the selection (or hold Ctrl)"]]
      .map(([k, l, t]) => `<button data-mode="${k}" title="${t}" data-testid="sel-mode-${k}">${l}</button>`).join("");
    b.onclick = e => { const x = e.target.closest("button[data-mode]"); if (!x) return; state.selMode = x.dataset.mode; selModeBar(); };
    $("#map-wrap").appendChild(b);
  }
  $$("button", b).forEach(x => x.classList.toggle("on", x.dataset.mode === state.selMode));
  const t = state.tool, compact = document.body.classList.contains("compact-ui");
  b.hidden = !state.model || !(t === "box" || t === "poly" || (t === "select" && (compact || state.selMode !== "new" || state.sel.ids.length > 0)));
}
function opFrom(o) { return o && o.ctrlKey ? "remove" : o && (o.shiftKey || o.metaKey) ? "add" : state.selMode; }
(function wireSelection() {
  const si = selectInside;                                            // features5's: every type, add or new
  selectInside = function (target, inside, add) {
    const op = selOpNext || (add ? "add" : state.selMode); selOpNext = null;
    if (op !== "remove") { si(target, inside, op === "add"); return; }
    const found = { nodes: new Set(), links: new Set(), catchments: new Set() }, all = target === "all";
    if (all || target === "nodes") for (const f of state.model.nodeFeat) if (inside(f.geometry.coordinates)) found.nodes.add(String(f.id));
    if (all || target === "links") for (const f of state.model.linkFeat) { const c = f.geometry.coordinates, a0 = c[0], a1 = c[c.length - 1]; if (inside([(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2])) found.links.add(String(f.id)); }
    if (all || target === "catchments") for (const f of state.model.catchFeat) if (inside(centroidOf(ringOf(f)))) found.catchments.add(String(f.id));
    const m = currentMix(), before = mixCount(m);
    for (const t of MIX_ORDER) m[t] = m[t].filter(i => !found[t].has(i));
    setMix(m); toast(`${before - mixCount(m)} taken out of the selection; ${mixCount(m)} left.`, "info");
  };
  const sc = selClick;
  selClick = function (table, id, multi) {
    if (multi || state.selMode === "new") return sc(table, id, multi);
    const m = currentMix(), a = m[table], k = a.indexOf(id);
    if (state.selMode === "add" && k < 0) a.push(id);
    if (state.selMode === "remove" && k >= 0) a.splice(k, 1);
    setMix(m);
  };
  const fp = finishPolySelect;
  finishPolySelect = function () { selOpNext = polyOp || state.selMode; polyOp = null; return fp(); };
  const st = setTool;
  setTool = function (t) { const r = st.apply(this, arguments); selModeBar(); if (typeof layoutPreview === "function") layoutPreview(); return r; };
  const ss = setSel;
  setSel = function () { const r = ss.apply(this, arguments); selModeBar(); vertexLayer(); return r; };
  (async () => {
    await mapReady;
    // Ctrl+drag with the Select tool removes, Shift+drag adds; in the Box tool a plain drag follows the switch
    map.on("mousedown", e => {
      const o = e.originalEvent || {}; if (o.button !== 0) return;
      if (state.tool === "box" || (state.tool === "select" && (o.shiftKey || o.ctrlKey))) selOpNext = opFrom(o);
      if (state.tool === "select" && o.ctrlKey && box) { box.target = "all"; box.nodes = false; }   // Ctrl no longer means "structures only"
    });
    map.on("click", e => { if (state.tool === "poly") { const o = e.originalEvent || {}; if (o.ctrlKey) polyOp = "remove"; else if (o.shiftKey) polyOp = "add"; } });
  })();
})();

/* ------------------------------------------------------------------ move a structure: drag it, or Move... then a tap */
let drag7 = null;
function startMovePick(id) {
  setTool("move"); state.movePick = id; setSel("nodes", [id]);
  if (document.body.classList.contains("compact-ui") && !ui.propsCollapsed) setProps(true);
  $("#hint").textContent = `Move ${id}: tap or click its new position (Esc cancels).`; showHint && showHint();
}
(async function wireMove() {
  await mapReady;
  map.addSource("verts", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addLayer({ id: "verts", type: "circle", source: "verts", paint: { "circle-radius": 5, "circle-color": "#fff", "circle-stroke-color": "#e6821e", "circle-stroke-width": 2 } });
  map.addSource("lay-prev", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addLayer({ id: "lay-prev", type: "line", source: "lay-prev", paint: { "line-color": "#e6821e", "line-width": 2, "line-dasharray": [2, 2] } });
  map.addLayer({ id: "lay-prev-pts", type: "circle", source: "lay-prev", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 4, "circle-color": "#e6821e" } });
  map.on("mousedown", e => {
    const o = e.originalEvent || {}; if (state.tool !== "select" || o.button !== 0 || o.shiftKey || o.ctrlKey || !state.model) return;
    const [tn] = pickTol();
    if (state.sel.table === "links" && state.sel.ids.length === 1) {               // a bend of the selected pipe
      const v = nearestVertex(state.sel.ids[0], e.point, tn);
      if (v) { drag7 = { kind: "vertex", id: state.sel.ids[0], k: v.k, from: e.point, moved: false }; map.dragPan.disable(); return; }
    }
    const n = nearestNode(e.point, tn);
    if (n && state.sel.table === "nodes" && state.sel.ids.length === 1 && state.sel.ids[0] === n.id) {
      drag7 = { kind: "node", id: n.id, from: e.point, moved: false }; map.dragPan.disable();
    }
  });
  map.on("mousemove", e => {
    if (!drag7) return;
    if (!drag7.moved && Math.hypot(e.point.x - drag7.from.x, e.point.y - drag7.from.y) < 4) return;
    drag7.moved = true; drag7.to = e.lngLat;
    map.getSource("drag").setData({ type: "Feature", geometry: { type: "Point", coordinates: [e.lngLat.lng, e.lngLat.lat] }, properties: {} });
  });
  map.on("mouseup", e => {
    if (!drag7) return; const d = drag7; drag7 = null; map.dragPan.enable();
    map.getSource("drag").setData({ type: "FeatureCollection", features: [] });
    if (!d.moved) return;
    suppressClick = true; setTimeout(() => { suppressClick = false; }, 80);
    if (d.kind === "node") enqueue(async () => { await moveNode(d.id, e.lngLat); toast(`${d.id} moved; its pipes follow (Ctrl+Z undoes).`, "info"); });
    else enqueue(async () => { const c = lineOf(d.id).slice(); c[d.k] = [e.lngLat.lng, e.lngLat.lat]; await setLine(d.id, c); });
  });
})();

/* ------------------------------------------------------------------ pipe bends */
const lineOf = id => { const f = state.model.links.get(id); return f ? f.geometry.coordinates.map(c => c.slice()) : []; };
async function setLine(id, coordsLL) { await exec({ op: "set_coords", id, coords_ll: coordsLL }); vertexLayer(); }
function nearestVertex(id, pt, tol) {
  const c = lineOf(id); let best = null;
  for (let k = 1; k < c.length - 1; k++) { const q = map.project(c[k]), d = Math.hypot(q.x - pt.x, q.y - pt.y); if (d <= tol && (!best || d < best.d)) best = { k, d }; }
  return best;
}
function vertexLayer() {
  const s = map && map.getSource && map.getSource("verts"); if (!s) return;
  const f = [];
  if (state.model && state.sel.table === "links" && state.sel.ids.length === 1) {
    const c = lineOf(state.sel.ids[0]); for (let k = 1; k < c.length - 1; k++) f.push({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: c[k] } });
  }
  s.setData({ type: "FeatureCollection", features: f });
}
function addBend(id, ll) {
  const c = lineOf(id), pt = map.project([ll.lng, ll.lat]); let best = 0, bd = Infinity;
  for (let k = 0; k < c.length - 1; k++) {
    const a = map.project(c[k]), b = map.project(c[k + 1]), dx = b.x - a.x, dy = b.y - a.y, L2 = dx * dx + dy * dy;
    const t = L2 ? Math.max(0, Math.min(1, ((pt.x - a.x) * dx + (pt.y - a.y) * dy) / L2)) : 0, d = Math.hypot(pt.x - (a.x + t * dx), pt.y - (a.y + t * dy));
    if (d < bd) { bd = d; best = k; }
  }
  c.splice(best + 1, 0, [ll.lng, ll.lat]); return enqueue(() => setLine(id, c));
}

/* ------------------------------------------------------------------ the layout tool: next point by right-click, bends */
layout.bend = false; layout.via = [];
let layMouse = null;
function layoutPreview() {
  const s = map && map.getSource && map.getSource("lay-prev"); if (!s) return;
  if (state.tool !== "layout" || !layout.last) { layout.via = []; s.setData({ type: "FeatureCollection", features: [] }); return; }
  const a = state.model && state.model.nodes.get(layout.last); if (!a) return;
  const pts = [a.geometry.coordinates, ...layout.via, ...(layMouse ? [layMouse] : [])], f = [];
  if (pts.length > 1) f.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: pts } });
  for (const v of layout.via) f.push({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: v } });
  s.setData({ type: "FeatureCollection", features: f });
}
const LAY_KINDS = [["manhole", "Manhole"], ["outfall", "Outfall"], ["wetwell", "Wet well"], ["pressure_junction", "Pressure junction"]];
function setLayoutNext(k) {
  if (k === "bend") { layout.bend = true; $("#hint").textContent = layout.last ? "Bend: each click adds a bend to the pipe; right-click > a structure type to place the next structure." : "Bend: click the structure the run starts from first."; return; }
  layout.bend = false; const s = $("#layout-node"); if (s && [...s.options].some(o => o.value === k)) { s.value = k; s.dispatchEvent(new Event("change")); } else layout.node = k;
  $("#hint").textContent = `Next point: ${(LAY_KINDS.find(x => x[0] === k) || [0, k])[1].toLowerCase()}.`;
}
function layoutMenu(x, y) {
  const cur = layout.bend ? "bend" : layout.node;
  ctxOpen(x, y, [{ head: "Layout" },
    { label: "Done: end the run", keys: "Esc", key: "lay-done", disabled: !layout.last, run: () => { layout.last = null; layout.via = []; layout.bend = false; layoutPreview(); $("#hint").textContent = HINTS.layout; } },
    ...(layout.via.length ? [{ label: "Remove the last bend", key: "lay-unbend", run: () => { layout.via.pop(); layoutPreview(); } }] : []),
    "-", { head: "Next point" },
    ...LAY_KINDS.map(([k, l]) => ({ label: (cur === k ? "● " : "○ ") + l, key: "lay-next-" + k, run: () => setLayoutNext(k) })),
    { label: (cur === "bend" ? "● " : "○ ") + "Bend (a vertex of the pipe, no structure)", key: "lay-next-bend", run: () => setLayoutNext("bend") }]);
}
(async function wireLayout() {
  await mapReady;
  map.on("mousemove", e => { if (state.tool === "layout" && layout.last) { layMouse = [e.lngLat.lng, e.lngLat.lat]; layoutPreview(); } });
  addEventListener("keydown", e => { if (e.key === "Escape") { layout.via = []; layout.bend = false; setTimeout(layoutPreview, 0); } });
})();

/* ------------------------------------------------------------------ the right-click menu: layout, bends, move */
(function wireCtx() {
  const cf = ctxForPoint, co = ctxOpen; let at = null;
  ctxForPoint = function (e) {
    if (state.tool === "layout" && state.model) { layoutMenu(e.originalEvent.clientX, e.originalEvent.clientY); return; }
    const [tn, tl] = pickTol(), nn = state.model ? nearestNode(e.point, tn) : null;
    at = { ll: e.lngLat, node: nn && nn.id, link: !nn && state.model ? (nearestLink(e.point, tl) || {}).id : null, point: e.point };
    try { return cf.apply(this, arguments); } finally { setTimeout(() => { at = null; }, 0); }
  };
  ctxOpen = function (x, y, items) {
    if (at && at.link && items.some(i => i && i.key === "split")) {
      const id = at.link, ll = at.ll, v = nearestVertex(id, at.point, pickTol()[0] + 4), bends = Math.max(0, lineOf(id).length - 2);
      const k = items.findIndex(i => i && i.key === "split");
      items.splice(k + 1, 0, { label: "Add a bend here", key: "bend-add", run: () => addBend(id, ll) },
        { label: "Remove this bend", key: "bend-del", disabled: !v, title: v ? "" : "Right-click on a bend", run: () => enqueue(() => { const c = lineOf(id); c.splice(v.k, 1); return setLine(id, c); }) },
        { label: `Straighten (remove ${bends ? "all " + bends : "the"} bends)`, key: "bend-clear", disabled: !bends, run: () => enqueue(() => setLine(id, [])) });
    }
    if (at && at.node && items.some(i => i && i.key === "find-connected")) {
      const id = at.node, k = items.findIndex(i => i && i.key === "find-connected");
      items.splice(k + 1, 0, { label: "Move...", key: "move-node", title: "Then click or tap its new position (or drag it while it is selected)", run: () => startMovePick(id) });
    }
    return co.apply(this, arguments);
  };
})();

/* ------------------------------------------------------------------ Properties: Move for a structure, Lift for a wet well */
(function wireProps() {
  const rp = renderProps;
  renderProps = function () {
    rp(); const host = $("#prop-grid"); if (!host || state.mix || state.sel.table !== "nodes" || state.sel.ids.length !== 1) return;
    const id = state.sel.ids[0], f = state.model.nodes.get(id); if (!f || host.querySelector(".p7")) return;
    const lifts = new Set((state.model.settings.lifts || []).map(String)), ww = f.properties.kind === "wetwell";
    host.insertAdjacentHTML("beforeend", `<div class="p7 trace-bar"><button data-testid="prop-move" title="Then click or tap its new position">Move...</button>` +
      (ww ? `<label class="rad" title="A lift raises the flow within a station's area: colour by pumping station merges it into the station downstream"><input type="checkbox" data-testid="prop-lift"${lifts.has(id) ? " checked" : ""}> a lift (not a pumping station)</label>` : "") + `</div>`);
    host.querySelector("[data-testid=prop-move]").onclick = () => startMovePick(id);
    const lb = host.querySelector("[data-testid=prop-lift]");
    if (lb) lb.onchange = () => enqueue(async () => {
      const L = new Set((state.model.settings.lifts || []).map(String)); if (lb.checked) L.add(id); else L.delete(id);
      await exec({ op: "set_setting", path: "lifts", value: [...L].sort() }); await loadModel(); mergeResults(); pushMap(); renderLegend();
    });
  };
})();

/* ------------------------------------------------------------------ the left dock: panes as tabs, widened by dragging */
const DOCK = { open: [], active: null, panes: {} };
function dockEl() {
  let d = $("#ldock"); if (d) return d;
  d = document.createElement("div"); d.id = "ldock"; d.hidden = true;
  d.innerHTML = `<div class="ld-head"><div class="ld-tabs" role="tablist"></div><button class="ld-x" title="Close this pane" data-testid="ldock-close">&times;</button></div><div class="ld-body"></div><div class="ld-grip" title="Drag to widen or narrow"></div>`;
  document.body.appendChild(d);
  d.querySelector(".ld-tabs").onclick = e => { const b = e.target.closest("button[data-pane]"); if (b) dockShow(b.dataset.pane); };
  d.querySelector(".ld-x").onclick = () => dockClose(DOCK.active);
  const grip = d.querySelector(".ld-grip");
  grip.addEventListener("pointerdown", e => {
    e.preventDefault(); try { grip.setPointerCapture(e.pointerId); } catch (x) { /* */ }
    const move = ev => { ui.ldockW = Math.max(240, Math.min(innerWidth - 200, ev.clientX)); dockLayout(); };
    const up = () => { grip.removeEventListener("pointermove", move); grip.removeEventListener("pointerup", up); saveUi(); setTimeout(() => map.resize(), 30); };
    grip.addEventListener("pointermove", move); grip.addEventListener("pointerup", up);
  });
  return d;
}
function dockLayout() {
  const r = $("#map-wrap").getBoundingClientRect(), on = DOCK.open.length > 0;
  document.body.style.setProperty("--dock-top", r.top + "px"); document.body.style.setProperty("--dock-bottom", Math.max(0, innerHeight - r.bottom) + "px");
  document.body.style.setProperty("--ldock-w", (ui.ldockW || 380) + "px");
  document.body.classList.toggle("ldock-on", on); document.body.classList.toggle("sym-docked", DOCK.open.includes("sym"));
  const d = dockEl(); d.hidden = !on;
  d.querySelector(".ld-tabs").innerHTML = DOCK.open.map(k => `<button data-pane="${k}" class="${k === DOCK.active ? "on" : ""}" data-testid="ldock-tab-${k}">${esc(DOCK.panes[k].title)}</button>`).join("");
  for (const k in DOCK.panes) { const el = DOCK.panes[k].el(); if (el) el.hidden = k !== DOCK.active || !DOCK.open.includes(k); }
  if (window.map) setTimeout(() => map.resize(), 30);
  if (typeof rbSyncToggles === "function") rbSyncToggles();
}
function dockShow(k) { DOCK.active = k; dockLayout(); if (DOCK.panes[k].onShow) DOCK.panes[k].onShow(); }
function dockOpen(k) {
  const p = DOCK.panes[k]; if (!p) return; const el = p.el(); if (!el) return;
  const body = dockEl().querySelector(".ld-body"); if (el.parentElement !== body) body.appendChild(el);
  if (!DOCK.open.includes(k)) DOCK.open.push(k);
  dockShow(k);
}
function dockClose(k) {
  DOCK.open = DOCK.open.filter(x => x !== k);
  if (DOCK.active === k) DOCK.active = DOCK.open[DOCK.open.length - 1] || null;
  dockLayout(); if (DOCK.active && DOCK.panes[DOCK.active].onShow) DOCK.panes[DOCK.active].onShow();
}
DOCK.panes.sym = { title: "Element Symbology", el: () => $("#dlg-sym .dlg") || $("#ldock .sym"), onShow: () => { if (state.model) { $("#dlg-sym").hidden = true; symRender(); } } };
DOCK.panes.bg = { title: "Background Layers", el: () => bgPane(), onShow: () => renderBg() };
(function wireDock() {
  symDock = function (on) { if (!state.model && on) { toast("Open a project first.", "info"); return; } if (on) dockOpen("sym"); else dockClose("sym"); };
  const so = symOpen;
  symOpen = function (type) { so.apply(this, arguments); $("#dlg-sym").hidden = true; dockOpen("sym"); };
  const sr = symRender;
  symRender = function () { const r = sr.apply(this, arguments); const d = $("#ldock"); if (d) tag(d); return r; };   // the pane's fields keep their test ids
  const bindClose = () => { const c = $("#sym-close"); if (c) c.onclick = () => dockClose("sym"); };
  bindClose(); setTimeout(bindClose, 0);
  addEventListener("resize", () => { if (DOCK.open.length) dockLayout(); });
})();

/* ------------------------------------------------------------------ Background Layers (as SewerGEMS's) */
function bgPane() {
  let p = $("#bg-pane"); if (p) return p;
  p = document.createElement("div"); p.id = "bg-pane"; p.className = "bg-pane"; p.hidden = true;
  p.innerHTML = `<h3>Background Layers</h3>
    <h4>Basemap</h4><div class="bg-base"></div>
    <h4>Layers <span class="muted">(drawn under the network; first in the list on top)</span></h4>
    <div class="row"><button data-act="add" data-testid="bg-add" title="A shapefile with its .shx, .dbf and .prj (or zipped), GeoPackage, GeoJSON, KML or DXF">Add layer...</button></div>
    <div class="bg-list" data-testid="bg-list"></div>
    <p class="muted small">Display only: a background layer is not part of the model. A DXF carries no coordinate system and is taken to be in the project's.</p>`;
  p.onclick = e => {
    const b = e.target.closest("[data-act]"); if (!b) return; const a = b.dataset.act, row = b.closest("[data-rid]"), rid = row ? row.dataset.rid : null;
    if (a === "add") {
      const i = document.createElement("input"); i.type = "file"; i.multiple = true; i.accept = ".shp,.shx,.dbf,.prj,.cpg,.zip,.gpkg,.geojson,.json,.kml,.dxf,.gml";
      i.onchange = () => enqueue(() => withBusy("Reading the layer...", async () => {
        if (!i.files.length || !state.pid) return;
        const fd = new FormData(); for (const f of i.files) fd.append("files", f);
        const r = await (await api(`/projects/${state.pid}/reference`, { method: "POST", body: fd })).json();
        await mapReady; state.refs = (state.refs || []).concat([r]); addRefToMap(r, state.refs.length - 1); refStyle(r); bgOrder(); renderBg(); renderRefs();
        toast(`${r.name}: ${r.count} features under the network.`, "info");
      }));
      i.click(); return;
    }
    const r = (state.refs || []).find(x => x.id === rid); if (!r) return;
    if (a === "zoom") { const b2 = bboxOf(r.geojson.features.flatMap(f => flatCoords(f.geometry))); if (b2) map.fitBounds([[b2[0], b2[1]], [b2[2], b2[3]]], { padding: 40, animate: false }); }
    if (a === "del") enqueue(async () => { await jpost(`/projects/${state.pid}/reference/${encodeURIComponent(r.id)}/delete`, {}); removeRefFromMap(r); state.refs = state.refs.filter(x => x !== r); renderBg(); renderRefs(); });
    if (a === "up" || a === "down") {
      const k = state.refs.indexOf(r), j = a === "up" ? k + 1 : k - 1;          // the list shows the top layer first
      if (j < 0 || j >= state.refs.length) return;
      [state.refs[k], state.refs[j]] = [state.refs[j], state.refs[k]]; bgOrder(); renderBg();
      enqueue(() => jpost(`/projects/${state.pid}/reference/order`, { ids: state.refs.map(x => x.id) }));
    }
  };
  p.onchange = p.oninput = e => {
    const t = e.target, row = t.closest("[data-rid]");
    if (t.dataset.mirror) {                                         // the basemap controls are the View tab's own: set them and let them act
      const o = $("#" + t.dataset.mirror); if (!o) return; if (o.type === "checkbox") o.checked = t.checked; else o.value = t.value;
      const h = o.type === "range" ? o.oninput : o.onchange; if (h && (o.type === "range" ? e.type === "input" : e.type === "change")) h({ target: o });
      return;
    }
    if (!row) return; const r = (state.refs || []).find(x => x.id === row.dataset.rid); if (!r) return;
    if (t.dataset.k === "visible") r.visible = t.checked; else if (t.dataset.k === "color") r.color = t.value; else if (t.dataset.k === "opacity") r.opacity = +t.value;
    refStyle(r); if (e.type === "change") { renderRefs(); enqueue(() => jpost(`/projects/${state.pid}/reference/${encodeURIComponent(r.id)}/style`, { color: r.color, opacity: r.opacity ?? 1, visible: r.visible })); }
  };
  return p;
}
const flatCoords = g => !g ? [] : g.type === "Point" ? [g.coordinates] : g.type === "LineString" || g.type === "MultiPoint" ? g.coordinates : g.type === "Polygon" || g.type === "MultiLineString" ? g.coordinates.flat() : g.type === "MultiPolygon" ? g.coordinates.flat(2) : [];
function refStyle(r) {
  if (!map.getLayer(`ref-${r.id}-line`)) return; const vis = r.visible !== false ? "visible" : "none", o = r.opacity ?? 1, c = r.color;
  for (const l of refLayerIds(r)) if (map.getLayer(l)) map.setLayoutProperty(l, "visibility", vis);
  map.setPaintProperty(`ref-${r.id}-fill`, "fill-color", c); map.setPaintProperty(`ref-${r.id}-fill`, "fill-opacity", 0.12 * o); map.setPaintProperty(`ref-${r.id}-fill`, "fill-outline-color", c);
  map.setPaintProperty(`ref-${r.id}-line`, "line-color", c); map.setPaintProperty(`ref-${r.id}-line`, "line-opacity", o);
  map.setPaintProperty(`ref-${r.id}-pt`, "circle-color", c); map.setPaintProperty(`ref-${r.id}-pt`, "circle-opacity", o);
}
function bgOrder() {                                    // state.refs: bottom first; each layer goes under the next
  const before = map.getLayer("route-halo") ? "route-halo" : undefined;
  for (const r of state.refs || []) for (const l of refLayerIds(r)) if (map.getLayer(l)) map.moveLayer(l, before);
}
function renderBg() {
  const p = bgPane(), base = p.querySelector(".bg-base"), bs = $("#basemap-select"), op = $("#basemap-opacity");
  if (bs && !base.dataset.done) {
    base.dataset.done = "1";
    base.innerHTML = `<label>Map <select data-mirror="basemap-select" data-testid="bg-basemap">${bs.innerHTML}</select></label>` +
      (op ? `<label>Opacity <input type="range" data-mirror="basemap-opacity" min="${op.min}" max="${op.max}" step="${op.step}"></label>` : "") +
      ($("#labels-toggle") ? `<label class="rad"><input type="checkbox" data-mirror="labels-toggle"> place and road names on the satellite</label>` : "") +
      ($("#hillshade-toggle") ? `<label class="rad"><input type="checkbox" data-mirror="hillshade-toggle"> hillshade (relief)</label>` : "");
  }
  for (const el of $$("[data-mirror]", base)) { const o = $("#" + el.dataset.mirror); if (!o) continue; if (o.type === "checkbox") el.checked = o.checked; else el.value = o.value; el.disabled = o.disabled; }
  const R = (state.refs || []).slice().reverse();
  p.querySelector(".bg-list").innerHTML = R.length ? R.map((r, i) => `<div class="bg-row" data-rid="${esc(r.id)}">
      <input type="checkbox" data-k="visible" title="Show" ${r.visible !== false ? "checked" : ""}><input type="color" data-k="color" value="${esc(r.color || "#d9480f")}" title="Colour">
      <span class="nm" title="${esc((r.count || 0) + " features" + (r.crs ? ", EPSG:" + r.crs : ""))}">${esc(r.name)}</span>
      <input type="range" data-k="opacity" min="0" max="1" step="0.05" value="${r.opacity ?? 1}" title="Opacity">
      <button class="mini" data-act="up" title="Up" ${i === 0 ? "disabled" : ""}>&#9650;</button><button class="mini" data-act="down" title="Down" ${i === R.length - 1 ? "disabled" : ""}>&#9660;</button>
      <button class="mini" data-act="zoom" title="Zoom to it">&#9635;</button><button class="mini" data-act="del" title="Remove">&times;</button></div>`).join("")
    : `<p class="muted">None yet. Plots, roads, a survey or contours (GIS or DXF) drawn under the network to work against.</p>`;
}
(function wireBg() {
  const ar = addRefToMap;
  addRefToMap = function (r, i) { const x = ar.apply(this, arguments); refStyle(r); return x; };
  const lr = loadRefs;
  loadRefs = async function () { const x = await lr.apply(this, arguments); bgOrder(); if (DOCK.open.includes("bg")) renderBg(); return x; };
})();
function openBackgroundLayers() { if (!state.pid) { toast("Open a project first.", "info"); return; } dockOpen("bg"); }

/* ------------------------------------------------------------------ colour by subnetwork: outfall, station, lift, every wet well */
const SUBNET = {
  subnet_out: { title: "Subnetwork by outfall", stop: () => false },
  subnet_st: { title: "Subnetwork by pumping station", stop: (k, id, L) => k === "wetwell" && !L.has(id) },
  subnet_lift: { title: "Subnetwork by lift", stop: (k, id, L) => k === "wetwell" && L.has(id), liftOnly: true },
  subnet_all: { title: "Subnetwork by every wet well and outfall", stop: k => k === "wetwell" || k === "storage" },
};
const SUBNET_COL = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22", "#7f7f7f", "#393b79", "#ad494a", "#637939", "#843c39", "#5254a3", "#e7969c"];
function subnetworks(mode) {
  const m = state.model, S = SUBNET[mode], L = new Set(((m.settings || {}).lifts || []).map(String)), leave = new Map();
  for (const f of m.linkFeat) { const p = f.properties, cur = leave.get(p.from_node); if (!cur || ["orifice", "weir"].includes(cur.properties.kind)) leave.set(p.from_node, f); }
  const kind = id => ((m.nodes.get(id) || {}).properties || {}).kind, memo = new Map();
  const root = n0 => {                                  // the first stop downstream (the node itself if it stops), else the end
    const path = []; let n = n0, r = null;
    for (let i = 0; i < 100000; i++) {
      if (memo.has(n)) { r = memo.get(n); break; }
      path.push(n);
      if (n !== n0 && S.stop(kind(n), n, L)) { r = n; break; }
      const f = leave.get(n); if (!f) { r = n; break; }
      n = f.properties.to_node; if (path.includes(n)) { r = n; break; }
    }
    for (const p of path) if (!(p !== n0 && false)) memo.set(p, r);
    return r;
  };
  // a structure belongs to the area that drains through it: a stop belongs to its own area
  const nodeArea = id => S.stop(kind(id), id, L) ? id : root(id);
  const linkArea = f => nodeArea(f.properties.from_node);
  const areas = new Map(), seen = [];
  for (const f of m.linkFeat) { const a = linkArea(f); if (a != null && !areas.has(a)) { areas.set(a, null); seen.push(a); } }
  seen.sort((a, b) => String(a).localeCompare(String(b), undefined, { numeric: true }));
  const col = {}; seen.forEach((a, i) => { col[a] = S.liftOnly && !L.has(a) ? GREY : SUBNET_COL[i % SUBNET_COL.length]; });
  return { nodeArea, linkArea, col, areas: seen };
}
function subnetApply() {
  const by = state.colorBy; if (!SUBNET[by] || !state.model) return;
  const s = subnetworks(by), cnt = {};
  for (const f of state.model.linkFeat) { const a = s.linkArea(f); f.properties._c = s.col[a] || GREY; f.properties._fail = 0; cnt[a] = (cnt[a] || 0) + 1; }
  for (const f of state.model.nodeFeat) { const a = s.nodeArea(String(f.id)); if (s.col[a] && s.col[a] !== GREY) f.properties._c = s.col[a]; }
  state.subnet = { mode: by, areas: s.areas, col: s.col, cnt };
  state.dirty.nodes = true; state.dirty.links = true;
}
(function wireSubnet() {
  const sel = $("#color-by");
  if (sel && !sel.querySelector("option[value=subnet_out]")) sel.insertAdjacentHTML("beforeend", `<optgroup label="Subnetwork">` +
    Object.entries(SUBNET).map(([k, v]) => `<option value="${k}">${v.title.replace("Subnetwork ", "subnetwork ")}</option>`).join("") + `</optgroup>`);
  for (const k in SUBNET) NO_FAIL.add(k);
  const mr = mergeResults; mergeResults = function () { const r = mr.apply(this, arguments); subnetApply(); return r; };
  const sa = symApply; symApply = function () { const r = sa.apply(this, arguments); subnetApply(); return r; };
  const rl = renderLegendPipes;
  renderLegendPipes = function () {
    if (!SUBNET[state.colorBy]) return rl.apply(this, arguments);
    const s = state.subnet, el = $("#legend"); if (!s || s.mode !== state.colorBy) { el.innerHTML = `<div class="t">${esc(SUBNET[state.colorBy].title)}</div>`; return; }
    const show = s.areas.filter(a => s.col[a] !== GREY), more = show.length - 14;
    el.innerHTML = `<div class="t">${esc(SUBNET[state.colorBy].title)} (${show.length})</div>` + show.slice(0, 14).map(a => `<div class="r"><span class="sw" style="background:${s.col[a]}"></span>${esc(a)} <span class="muted">${s.cnt[a] || 0} pipes</span></div>`).join("") +
      (more > 0 ? `<div class="r muted">and ${more} more</div>` : "") + (state.colorBy === "subnet_lift" ? `<div class="r"><span class="sw" style="background:${GREY}"></span>not in a lift's area</div>` : "") +
      (state.colorBy !== "subnet_out" && !((state.model.settings || {}).lifts || []).length && state.colorBy !== "subnet_all" ? `<div class="r muted">No wet well is marked as a lift (its Properties)</div>` : "");
  };
})();

/* ------------------------------------------------------------------ a link per model; recent models in this browser */
const RECENT_KEY = "w19.recent";
function recentModels() { try { return JSON.parse(localStorage.getItem(RECENT_KEY) || "[]"); } catch (e) { return []; } }
function rememberModel() {
  if (!state.pid || !state.info) return;
  try { const R = recentModels().filter(r => r.id !== state.pid); R.unshift({ id: state.pid, name: state.info.name, t: Date.now() }); localStorage.setItem(RECENT_KEY, JSON.stringify(R.slice(0, 20))); } catch (e) { /* not kept */ }
}
function modelLink() { const u = new URL(location.href); u.search = ""; u.hash = ""; u.searchParams.set("p", state.pid); u.searchParams.set("s", state.sid || "base"); return u.href; }
async function copyModelLink() {
  if (!state.pid) { toast("Open a project first.", "info"); return; }
  const l = modelLink();
  try { await navigator.clipboard.writeText(l); toast("This model's link is copied: open it in any browser to come back to this model and scenario.", "info"); }
  catch (e) { await askText("This model's link", "Copy it (Ctrl+C): it opens this model and scenario in any browser", l); }
}
async function openRecent() {
  const R = recentModels(), d = dlg("dlg-recent", "Recent models", false), b = d.querySelector(".body");
  d.querySelector("[data-act=ok]").hidden = true;
  b.innerHTML = R.length ? `<p class="muted">The models opened in this browser. A model stays on the server while it is in use; one closed there no longer opens.</p>` +
      R.map(r => `<div class="rec"><button data-id="${esc(r.id)}" data-testid="recent-${esc(r.id)}">${esc(r.name)}</button> <span class="muted">${new Date(r.t).toLocaleString()}</span></div>`).join("")
    : `<p class="muted">None yet: the models you open in this browser are listed here.</p>`;
  d.hidden = false;
  d.onclick = e => {
    if (e.target.dataset.act === "close") { d.hidden = true; return; }
    const x = e.target.closest("button[data-id]"); if (!x) return; d.hidden = true;
    enqueue(() => withBusy("Opening...", async () => {
      try { await openProject(await jget(`/projects/${encodeURIComponent(x.dataset.id)}`)); }
      catch (err) { toast("That model is no longer open on the server.", "err"); try { localStorage.setItem(RECENT_KEY, JSON.stringify(recentModels().filter(r => r.id !== x.dataset.id))); } catch (q) { /* */ } }
    }));
  };
}
(function wireLinks() {
  const op = openProject;
  openProject = async function () { const r = await op.apply(this, arguments); rememberModel(); return r; };
})();

/* ------------------------------------------------------------------ Find: elements and tools */
function toolIndex() {
  const out = [];
  for (const pg of $$(".rb-page")) {
    const tab = pg.dataset.tab, tl = ($(`#rb-tab-${tab}`) || {}).textContent || tab;
    for (const b of $$(".rb-btn", pg)) {
      const label = (b.querySelector("span") || {}).textContent || "", title = b.title || "";
      if (!label.trim() && !title.trim()) continue;
      out.push({ kind: "tool", label: label.trim() || title, where: tl.trim(), text: `${label} ${title} ${tl}`.toLowerCase(), run: () => { const t = $(`#rb-tab-${tab}`); if (t) t.click(); setTimeout(() => b.click(), 30); } });
    }
  }
  for (const [g] of (typeof SET_GROUPS !== "undefined" ? SET_GROUPS : [])) out.push({ kind: "tool", label: g, where: "Settings", text: `${g} settings`.toLowerCase(), run: () => openSettingsGroup(g) });
  const extra = [["Background Layers", "View", "background layers basemap reference shapefile dxf", openBackgroundLayers], ["Copy this model's link", "File", "link share url address copy", copyModelLink],
    ["Recent models", "File", "recent open models history", openRecent], ["TRex: ground levels from terrain", "Tools", "trex terrain ground level dem geotiff vrt copernicus contours dxf elevation", () => openTRex()]];
  for (const [l, w, t, run] of extra) out.push({ kind: "tool", label: l, where: w, text: `${l} ${t}`.toLowerCase(), run });
  return out;
}
function findList(q) {
  let box = $("#find-list");
  if (!box) { box = document.createElement("div"); box.id = "find-list"; box.setAttribute("role", "listbox"); document.body.appendChild(box); }
  const lq = q.trim().toLowerCase(); if (!lq) { box.hidden = true; return []; }
  const words = lq.split(/\s+/), hits = [];
  if (state.model) for (const t of ["nodes", "links", "catchments"]) for (const k of tmap(t).keys()) { if (k.toLowerCase().includes(lq)) hits.push({ kind: "el", label: k, where: { nodes: "structure", links: "pipe", catchments: "catchment" }[t], run: () => { setSel(t, [k], { zoom: true }); $("#find-input").value = k; } }); if (hits.length > 6) break; }
  const seen = new Set();
  for (const x of toolIndex()) if (words.every(w => x.text.includes(w)) && !seen.has(x.label + x.where)) { seen.add(x.label + x.where); hits.push(x); }
  const show = hits.slice(0, 12);
  box.innerHTML = show.map((h, i) => `<button data-i="${i}" class="${h.kind}" data-testid="find-hit-${i}">${h.kind === "tool" ? "&#9881; " : ""}${esc(h.label)} <span class="muted">${esc(h.where)}</span></button>`).join("") || `<div class="muted">Nothing matches "${esc(q)}".</div>`;
  const r = $("#find-wrap").getBoundingClientRect();
  Object.assign(box.style, { top: (r.bottom + 4) + "px", left: Math.max(6, Math.min(r.left, innerWidth - 330)) + "px" }); box.hidden = false;
  box.onmousedown = e => { const b = e.target.closest("button[data-i]"); if (!b) return; e.preventDefault(); box.hidden = true; $("#find-input").blur(); show[+b.dataset.i].run(); };
  return show;
}
(function wireFind() {
  const inp = $("#find-input"); if (!inp) return;
  inp.placeholder = "Find an element or a tool";
  $("#find-wrap").title = "Find an element by its ID, or a tool by its name (Ctrl+F)";
  let shown = [];
  inp.addEventListener("input", () => { shown = findList(inp.value); });
  inp.addEventListener("keydown", e => {
    if (e.key === "Enter" && shown.length && !(state.model && ["nodes", "links", "catchments"].some(t => tmap(t).has(inp.value.trim())))) { e.preventDefault(); e.stopImmediatePropagation(); const h = shown[0]; $("#find-list").hidden = true; inp.blur(); h.run(); }
  }, true);
  inp.addEventListener("blur", () => setTimeout(() => { const b = $("#find-list"); if (b) b.hidden = true; }, 150));
})();

/* ------------------------------------------------------------------ a SewerGEMS model from any device */
const SG_MINE = "w19.sgmine";
const sgMine = () => { try { return JSON.parse(localStorage.getItem(SG_MINE) || "[]"); } catch (e) { return []; } };
(function wireSg() {
  const rs = refreshSg;
  refreshSg = async function () {
    if (!ENV.local) {
      try { sgData = await jget(`/sewergems/models?mine=${encodeURIComponent(sgMine().join(","))}`); } catch (e) { $("#sg-list").textContent = e.message; return; }
      const d = sgData, w = d.watcher, list = $("#sg-list");
      $("#sg-watch").innerHTML = w.alive ? `<span class="ok">&#9679;</span> The SewerGEMS link is running.` : `<span class="bad">&#9679;</span> The SewerGEMS link is not running at the moment: a model picked now waits until it runs.`;
      list.innerHTML = d.exports.length ? d.exports.map(e => `<button data-name="${esc(e.name)}" id="sg-${esc(e.name)}">${esc(e.name)} (${e.scenarios} scenarios)</button>`).join("") : `<p data-testid="sg-empty" class="muted">None yet: choose a model's files above.</p>`;
      tag(list); renderSgJobs(); return;
    }
    return rs.apply(this, arguments);
  };
  const dlgEl = $("#dlg-sg .dlg"); if (!dlgEl || $("#sg-upload")) return;
  $("#sg-watch").insertAdjacentHTML("afterend", `<div class="sg-up"><h4>From this device</h4><p class="muted">Pick the folder the model is in: the app finds the .stsw and its .stsw.sqlite (a browser cannot reach a file beside the one you pick, so it asks for the folder). Or pick both files, or one zip of them. SewerGEMS reads a copy; your files are not changed. Through a shared link a file can be up to about 100 MB: zip a larger model.</p>
    <div class="row"><button id="sg-folder" class="primary" data-testid="sg-folder" title="The app finds the .stsw and its .stsw.sqlite in the folder; only those two files are read">Choose the model's folder...</button><button id="sg-upload" data-testid="sg-upload">or the model's files...</button><label class="chk"><input type="checkbox" id="sg-up-run"> compute every scenario first</label></div></div>`);
  // the model is two files: a .stsw picked alone is completed by a second pick of its .stsw.sqlite (a browser cannot
  // fetch the file beside it); a file SewerGEMS keeps locked is named, not sent half-read (the engineer, 2026-11-24)
  const send = files => enqueue(() => withBusy("Sending the model...", async () => {
    for (const f of files) {
      try { await f.slice(0, 16).arrayBuffer(); }
      catch (x) { toast(`${f.name} cannot be read: if the model is open in SewerGEMS, close it (or Save As a copy) and pick the files again.`); return; }
    }
    const fd = new FormData(); for (const f of files) fd.append("files", f);
    try {
      const r = await (await api(`/sewergems/upload?run=${$("#sg-up-run").checked}`, { method: "POST", body: fd })).json();
      try { localStorage.setItem(SG_MINE, JSON.stringify([...new Set([r.tag, ...sgMine()])].slice(0, 30))); } catch (e) { /* */ }
      $("#sg-up-more").innerHTML = "";
      toast(`${r.name} (${r.mb} MB) is with SewerGEMS: it is listed below when ready (from seconds to minutes).`, "info"); await refreshSg(); sgPoll();
    } catch (x) { toast(x.message || String(x)); }
  }));
  const pick = (accept, then) => { const i = document.createElement("input"); i.type = "file"; i.multiple = true; i.accept = accept; i.onchange = () => then([...i.files]); i.click(); };
  $("#sg-upload").insertAdjacentHTML("afterend", `<span id="sg-up-more" data-testid="sg-up-more"></span>`);
  // the model's folder: every .stsw there with its .stsw.sqlite; one is sent at once, several are offered (2026-11-24)
  const offer = models => {
    if (!models.length) { toast("No SewerGEMS model in that folder: it needs a .stsw with its .stsw.sqlite beside it.", "info"); return; }
    if (models.length === 1) { models[0].get().then(send); return; }
    const host = $("#sg-up-more");
    host.innerHTML = ` ${models.length} models there: ` + models.map((m, k) => `<button data-k="${k}" data-testid="sg-up-model-${k}">${esc(m.name)}</button>`).join(" ");
    host.onclick = e => { const b = e.target.closest("button[data-k]"); if (b) { host.onclick = null; models[+b.dataset.k].get().then(send); } };
  };
  $("#sg-folder").onclick = async () => {
    $("#sg-up-more").innerHTML = "";
    if (window.showDirectoryPicker) {                                  // reads only the two files it sends
      let h; try { h = await window.showDirectoryPicker({ mode: "read" }); } catch (x) { if (x.name !== "AbortError") toast(`That folder cannot be opened (${x.message}): pick the model's own folder, or its files.`); return; }
      const all = new Map();
      for await (const [n, fh] of h.entries()) if (fh.kind === "file" && /\.stsw(\.sqlite)?$/i.test(n)) all.set(n.toLowerCase(), fh);
      offer([...all.keys()].filter(k => k.endsWith(".stsw") && all.has(k + ".sqlite")).sort().map(k => ({ name: all.get(k).name, get: async () => [await all.get(k).getFile(), await all.get(k + ".sqlite").getFile()] })));
      return;
    }
    const i = document.createElement("input"); i.type = "file"; i.webkitdirectory = true;          // other browsers: the folder's list
    i.onchange = () => { const all = new Map([...i.files].filter(f => !f.webkitRelativePath || f.webkitRelativePath.split("/").length === 2).map(f => [f.name.toLowerCase(), f]));
      offer([...all.keys()].filter(k => k.endsWith(".stsw") && all.has(k + ".sqlite")).sort().map(k => ({ name: all.get(k).name, get: async () => [all.get(k), all.get(k + ".sqlite")] }))); };
    i.click();
  };
  $("#sg-upload").onclick = () => pick(".stsw,.sqlite,.zip", files => {
    if (!files.length) return;
    const st = files.find(f => /\.stsw$/i.test(f.name)), zip = files.some(f => /\.zip$/i.test(f.name));
    const has = st && files.some(f => f.name.toLowerCase() === st.name.toLowerCase() + ".sqlite");
    if (!st || has || zip) { send(files); return; }
    const host = $("#sg-up-more");
    host.innerHTML = ` ${esc(st.name)} picked; now its data file: <button data-testid="sg-up-sqlite">Choose ${esc(st.name)}.sqlite...</button>`;
    host.querySelector("button").onclick = () => pick(".sqlite", more => {
      const q = more.find(f => f.name.toLowerCase() === st.name.toLowerCase() + ".sqlite");
      if (!q) { toast(`That is not ${st.name}.sqlite: pick the file of that name beside the model.`); return; }
      send([st, q]);
    });
  });
  for (const el of [$("#sg-filter"), $("#sg-models"), $("#sg-guest"), $("#sg-export-path")]) if (el) (el.closest(".row") || el).classList.add("local-only");
  for (const h of $$("#dlg-sg h4")) if (/Export from SewerGEMS/.test(h.textContent)) h.classList.add("local-only");
  const rl = $("#sg-run"); if (rl) (rl.closest("label") || rl).classList.add("local-only");
})();

/* ------------------------------------------------------------------ wiring that needs the ribbon built */
(function wireLater() {
  const go = () => {
    const ribBtn = $$(".rb-btn").find(b => /Reference layers/.test(b.textContent));
    if (ribBtn) {                                                   // the View tab's button opens the pane (its old pop-up stays reachable nowhere else)
      ribBtn.querySelector("span").textContent = "Background Layers"; ribBtn.title = "Basemap and the layers drawn under the network (as SewerGEMS's Background Layers)";
      ribBtn.addEventListener("click", e => { e.stopImmediatePropagation(); openBackgroundLayers(); }, true);
    }
    const page = $("#rb-page-file");
    if (page && !$("[data-testid=rb-copy-link]")) {
      page.appendChild(rbGroup("Share", [rbBtn({ icon: "copy", label: "Copy link", big: true, title: "This model's link: it opens this model and scenario in any browser", run: copyModelLink, id: "rb-copy-link" }),
        rbBtn({ icon: "open", label: "Recent", big: true, title: "The models opened in this browser", run: openRecent, id: "rb-recent" })]));
    }
    selModeBar(); dockLayout();
  };
  if (document.readyState === "complete") setTimeout(go, 0); else addEventListener("load", () => setTimeout(go, 0));
})();

/* ------------------------------------------------------------------ the assistant: steps shown while it works, plain words */
const TOOL_WORDS = {
  list_projects: "Listing the open projects", project_summary: "Reading the scenario's summary", query_links: "Looking through the pipes",
  get_element: "Reading an element", explain_link: "Checking a pipe against the design rules", make_scenario: "Making a scenario to work in",
  design_scenario: "Designing a copy of the scenario", storm_scenario: "Running the storm on SWMM", lookup_criterion: "Looking up the guideline",
  show_on_map: "Pointing at it on the map", show_profile: "Drawing a long section", list_folders: "Listing your folders", list_files: "Reading a folder",
  inspect_layer: "Reading a GIS layer", read_text_file: "Reading a file", new_project: "Starting a project", import_network: "Building a network from GIS layers",
  import_swmm: "Reading a SWMM file", loads_from_layer: "Loading the network from a layer", terrain_from_file: "Taking ground levels from a terrain",
  edit_model: "Editing its copy of the model", run_analysis: "Checking and running the model",
};
function toolWords(name, input) {
  const base = TOOL_WORDS[name] || (name.startsWith("qgis_") ? "Reading the open QGIS project" : name.replace(/_/g, " ").replace(/^./, c => c.toUpperCase()));
  const i = input || {}, what = i.ids && i.ids.length ? `: ${i.ids.slice(0, 3).join(", ")}${i.ids.length > 3 ? "..." : ""}` : i.start ? `: ${i.start}${i.end ? " to " + i.end : ""}` : i.query ? `: "${String(i.query).slice(0, 40)}"` : "";
  return base + what;
}
function asstStepsHtml(steps, sec) {
  const tools = steps.filter(s => s.kind === "tool"), turns = steps.filter(s => s.kind === "turn").length;
  return `<div class="asst-live" data-testid="asst-live"><div class="muted">${tools.length ? "Working" : "Thinking"}... ${sec != null ? sec + " s" : ""}</div>` +
    tools.map((s, k) => `<div class="tc${k === tools.length - 1 ? " now" : ""}">${esc(toolWords(s.name, s.input))}</div>`).join("") +
    (turns > tools.length + 1 ? "" : "") + `</div>`;
}
async function asstAsk(body, onSteps) {
  const t0 = Date.now(), st = await jpost("/assistant/start", body);
  if (!st.job) return st;                                             // an answer that came back at once (a refusal, a limit)
  for (;;) {
    await new Promise(r => setTimeout(r, 700));
    const j = await jget(`/assistant/job/${st.job}`);
    if (j.state !== "done") { onSteps(j.steps || [], j.seconds); continue; }
    if (j.error) throw new Error(j.error);
    return Object.assign(j.out, { seconds: Math.round((Date.now() - t0) / 1000) });
  }
}

/* ------------------------------------------------------------------ a long press is the right-click on a phone */
let ctxAt = 0;
(function wireLongPress() {
  const cf = ctxForPoint;
  ctxForPoint = function () { ctxAt = Date.now(); return cf.apply(this, arguments); };   // Android sends contextmenu itself
  (async () => {
    await mapReady; const cv = map.getCanvasContainer(); let lp = null, fired = 0;
    map.off("movestart", ctxClose); map.on("movestart", () => { if (Date.now() - ctxAt > 1000) ctxClose(); });   // a held finger starts a "move"
    cv.addEventListener("touchstart", e => {
      if (e.touches.length !== 1) { clearTimeout(lp && lp.t); lp = null; return; }
      const t = e.touches[0], r = cv.getBoundingClientRect(), x = t.clientX, y = t.clientY;
      lp = { x, y, t: setTimeout(() => {
        if (!lp || Date.now() - ctxAt < 900) return;                 // the browser already opened it
        const point = new maplibregl.Point(x - r.left, y - r.top), lngLat = map.unproject(point);
        suppressClick = true; setTimeout(() => { suppressClick = false; }, 400);
        ctxForPoint({ point, lngLat, originalEvent: { clientX: x, clientY: y, preventDefault() {} } }); lp = null; fired = Date.now();
        const eat = ev => { if (Date.now() - fired < 800 && !(ev.target.closest && ev.target.closest("#ctx-menu"))) { ev.stopPropagation(); ev.preventDefault(); } };
        document.addEventListener("click", eat, true); setTimeout(() => document.removeEventListener("click", eat, true), 800);   // the finger's lift is not a click
      }, 650) };
    }, { passive: true });
    cv.addEventListener("touchmove", e => { if (lp && Math.hypot(e.touches[0].clientX - lp.x, e.touches[0].clientY - lp.y) > 10) { clearTimeout(lp.t); lp = null; } }, { passive: true });
    cv.addEventListener("touchend", e => { if (lp) { clearTimeout(lp.t); lp = null; } else if (Date.now() - fired < 800 && e.cancelable) e.preventDefault(); }, { passive: false });
  })();
})();
