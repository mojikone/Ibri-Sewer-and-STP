"use strict";
/* Sewer and stormwater network editor: browser interface for the general API (/api/g). Plain JS + MapLibre GL. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const API = "/api/g";
const M_LON = 111319.49, M_LAT = 110574.0;
const PAGE = 200;
const num = (v, d = 3) => (v == null || Number.isNaN(v)) ? "" : (typeof v === "number" ? String(+v.toFixed(d)) : String(v));

const state = {
  pid: null, info: null, sid: "base", model: null, results: null, summary: null,
  sel: { table: null, ids: [] }, tool: "select", colorBy: "v_ms", pipeStart: null, movePick: null,
  pending: 0, rev: 0, tab: "nodes", tools: [], toolout: null, dirty: { nodes: true, links: true },
  table: { nodes: { sort: "id", dir: 1, filter: "", page: 0 }, links: { sort: "id", dir: 1, filter: "", page: 0 },
           results: { sort: "id", dir: 1, filter: "", page: 0 }, toolout: { sort: "id", dir: 1, filter: "", page: 0 } },
  view: { nodes: [], links: [], results: [], toolout: [] }, anchor: {},
  draw: null, catchPending: null, storm: null,
  rain: { step_min: 5, duration_min: 60, mode: "idf", idf: [], series: [] },
};
const tmap = table => state.model ? (table === "nodes" ? state.model.nodes : table === "links" ? state.model.links : state.model.catchments) : new Map();
let map, mapReady, chain = Promise.resolve();

/* ------------------------------------------------------------------ plumbing */
async function api(path, opts) {
  const r = await fetch(API + path, opts);
  if (!r.ok) {
    let t = await r.text();
    try { const j = JSON.parse(t); t = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail || j); } catch (e) { /* keep text */ }
    throw new Error(t.slice(0, 400));
  }
  return r;
}
const jget = async p => (await api(p)).json();
const jpost = async (p, b) => (await api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) })).json();
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => { t.hidden = true; }, 6000);
}
function enqueue(fn) {
  state.pending++; document.body.dataset.pending = state.pending;
  const p = chain.then(fn).catch(e => { console.warn(e); toast(e.message || String(e)); })
    .finally(() => { state.pending--; document.body.dataset.pending = state.pending; });
  chain = p; return p;
}
const tag = root => $$("[id]", root || document).forEach(e => { if (!e.dataset.testid) e.dataset.testid = e.id; });
const base = () => `/projects/${state.pid}/scenarios/${state.sid}`;
const scenario = () => state.info && state.info.scenarios.find(s => s.id === state.sid);
function busy(on, text) { $("#busy").hidden = !on; if (text) $("#busy-text").textContent = text; }

/* ------------------------------------------------------------------ colours and legend */
const GREY = "#9aa5b1";
const SCALES = {
  dn_mm: { title: "Size DN (mm)", bins: [[250, "up to 250", "#9ecae1"], [315, "280-315", "#6baed6"], [400, "355-400", "#4292c6"], [500, "450-500", "#2171b5"], [630, "560-630", "#6a51a3"], [800, "710-800", "#8c2d8c"], [1000, "900-1000", "#b0307a"], [1e9, "over 1000", "#7a0e3a"]] },
  storm_q: { title: "Storm peak flow", bins: [] },
  storm_cap: { title: "Storm fullness (capacity)", bins: [[0.3, "below 0.30", "#c6dbef"], [0.6, "0.30-0.60", "#6baed6"], [0.9, "0.60-0.90", "#fdae61"], [0.999, "0.90-1.00", "#f46d43"], [1e9, "full (surcharged)", "#a50026"]] },
  storm_flood: { title: "Flooding", bins: [] },
  v_ms: { title: "Velocity (m/s)", bins: [[0.75, "below 0.75", "#2166ac"], [1.5, "0.75-1.5", "#66bd63"], [2.5, "1.5-2.5", "#fdae61"], [3.0, "2.5-3.0", "#f46d43"], [1e9, "over 3.0", "#a50026"]] },
  d_over_D: { title: "d/D", bins: [[0.3, "below 0.30", "#c6dbef"], [0.5, "0.30-0.50", "#6baed6"], [0.7, "0.50-0.70", "#fdae61"], [0.8, "0.70-0.80", "#f46d43"], [1e9, "over 0.80", "#a50026"]] },
  q_ls: { title: "Flow (L/s)", bins: [[1, "below 1", "#c6dbef"], [5, "1-5", "#9ecae1"], [10, "5-10", "#6baed6"], [25, "10-25", "#3182bd"], [100, "25-100", "#6a51a3"], [1e9, "over 100", "#4a1486"]] },
};
function colourFor(by, v) {
  if (by === "none" || v == null || !SCALES[by]) return GREY;
  for (const b of SCALES[by].bins) if (v <= b[0]) return b[2];
  return GREY;
}
const stormNow = () => state.storm && state.storm.sid === state.sid ? state.storm.data : null;
function renderLegend() {
  const el = $("#legend"), by = state.colorBy, stale = by.startsWith("storm") && state.storm && state.storm.stale;
  if (by.startsWith("storm") && !stormNow()) { el.innerHTML = `<div class="t">${SCALES[by].title}</div><div class="r muted">run Tools &gt; Run on EPA SWMM first</div>`; return; }
  const rows = by === "none" || by === "storm_flood" ? [] : SCALES[by].bins.map(b => [b[2], b[1]]);
  el.innerHTML = (by === "none" ? "" : `<div class="t">${SCALES[by].title}${stale ? " (before the last edit)" : ""}</div>`) +
    rows.map(r => `<div class="r"><span class="sw" style="background:${r[0]}"></span>${esc(r[1])}</div>`).join("") +
    (by === "storm_flood" ? `<div class="r"><span class="sw" style="background:#d7301f;height:9px;border-radius:5px;width:9px"></span>node flooding</div>` : "") +
    `<div class="r"><span class="sw" style="background:#d7301f"></span>failing (drawn on top)</div>` +
    `<div class="r"><span class="sw" style="background:repeating-linear-gradient(90deg,#7b3fa0 0 5px,transparent 5px 8px)"></span>pump</div>`;
}

/* ------------------------------------------------------------------ map */
function initMap() {
  map = new maplibregl.Map({
    container: "map", center: [0.001, 0.0005], zoom: 17, boxZoom: false, doubleClickZoom: false, attributionControl: true,
    style: {
      version: 8, glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
      sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "&copy; OpenStreetMap contributors", maxzoom: 19 } },
      layers: [{ id: "bg", type: "background", paint: { "background-color": "#f3f5f8" } },
               { id: "osm", type: "raster", source: "osm", layout: { visibility: "none" } }],
    },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
  mapReady = new Promise(res => {
    let done = false; const go = () => { if (!done) { done = true; res(); } };
    map.on("load", go);
    const t = setInterval(() => { if (map.style && map.style._loaded) { clearInterval(t); go(); } }, 50);
  }).then(() => {
    const E = { type: "FeatureCollection", features: [] };
    for (const id of ["grid", "catch", "catch-links", "drawpoly", "links", "nodes", "sel-links", "sel-nodes", "drag"]) map.addSource(id, { type: "geojson", data: E, tolerance: 0.4 });
    map.addLayer({ id: "grid", type: "line", source: "grid", paint: { "line-color": "#d6dde6", "line-width": 1 } });
    map.addLayer({ id: "catch", type: "fill", source: "catch", paint: { "fill-color": "#4aa3a2", "fill-opacity": 0.22 } });
    map.addLayer({ id: "catch-line", type: "line", source: "catch", paint: { "line-color": "#2d7f7e", "line-width": 1.5 } });
    map.addLayer({ id: "catch-links", type: "line", source: "catch-links", paint: { "line-color": "#2d7f7e", "line-width": 1.2, "line-dasharray": [1, 2] } });
    map.addLayer({ id: "drawpoly-fill", type: "fill", source: "drawpoly", filter: ["==", ["geometry-type"], "Polygon"], paint: { "fill-color": "#e6821e", "fill-opacity": 0.2 } });
    map.addLayer({ id: "drawpoly-line", type: "line", source: "drawpoly", paint: { "line-color": "#e6821e", "line-width": 2, "line-dasharray": [2, 1] } });
    map.addLayer({ id: "drawpoly-pts", type: "circle", source: "drawpoly", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 4, "circle-color": "#e6821e" } });
    const w = k => ["interpolate", ["linear"], ["zoom"], 10, 1 * k, 15, 2.2 * k, 19, 5 * k];
    map.addLayer({ id: "links-base", type: "line", source: "links", layout: { "line-cap": "round" }, paint: { "line-color": ["get", "_c"], "line-width": w(1) } });
    map.addLayer({ id: "links-fail", type: "line", source: "links", filter: ["==", ["get", "_fail"], 1], paint: { "line-color": "#d7301f", "line-width": w(1.4) } });
    map.addLayer({ id: "links-pump", type: "line", source: "links", filter: ["==", ["get", "kind"], "pump"], paint: { "line-color": "#7b3fa0", "line-width": w(1.5), "line-dasharray": [2, 1.5] } });
    map.addLayer({ id: "sel-links-casing", type: "line", source: "sel-links", paint: { "line-color": "#fff", "line-width": 9 } });
    map.addLayer({ id: "sel-links", type: "line", source: "sel-links", paint: { "line-color": "#00b3c7", "line-width": 5 } });
    const kc = ["match", ["get", "kind"], "outfall", "#123e7c", "wetwell", "#7b3fa0", "storage", "#1b9e77", "junction", "#c9a227", "#8a94a0"];
    const fl = ["==", ["coalesce", ["get", "_fl"], 0], 1];
    map.addLayer({ id: "nodes", type: "circle", source: "nodes", paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, ["case", fl, 3.5, 1.6], 15, ["case", fl, 7, 4], 19, ["case", fl, 12, 8]], "circle-color": ["case", fl, "#d7301f", kc], "circle-stroke-color": "#fff", "circle-stroke-width": 1.2 } });
    map.addLayer({ id: "nodes-label", type: "symbol", source: "nodes", minzoom: 15.5, layout: { "text-field": ["get", "id"], "text-size": 11, "text-offset": [0, 1.1], "text-anchor": "top", "text-font": ["Open Sans Regular"], "text-allow-overlap": false }, paint: { "text-color": "#1d2733", "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    map.addLayer({ id: "sel-nodes", type: "circle", source: "sel-nodes", paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 5, 19, 12], "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": ["case", ["==", ["get", "_pend"], 1], "#e6821e", "#00b3c7"], "circle-stroke-width": 3 } });
    map.addLayer({ id: "drag", type: "circle", source: "drag", paint: { "circle-radius": 8, "circle-color": "rgba(230,130,30,.35)", "circle-stroke-color": "#e6821e", "circle-stroke-width": 2 } });
    map.on("moveend", updateGrid);
    updateGrid();
  });
  map.on("click", e => { if (suppressClick) return; if (state.tool === "move") return; enqueue(() => act(e.lngLat, e.originalEvent)); });
  map.on("dblclick", e => { e.preventDefault(); if (state.tool === "catchment") finishCatchment(); });
  map.on("mousemove", e => { map.getCanvas().style.cursor = state.pid ? (state.tool === "select" ? "" : "crosshair") : ""; if (dragging) dragMove(e.lngLat); });
  map.on("mousedown", e => dragStart(e));
  map.on("mouseup", e => dragEnd(e));
  new ResizeObserver(() => map.resize()).observe($("#map-wrap"));
}
let dragging = null, suppressClick = false;
function dragStart(e) {
  if (state.tool !== "move" || !state.pid) return;
  const n = nearestNode(e.point, 12); if (!n) return;
  dragging = { id: n.id, moved: false, from: e.point }; map.dragPan.disable();
}
function dragMove(ll) {
  const d = dragging; d.moved = true;
  const s = map.getSource("drag"); if (s) s.setData({ type: "Feature", geometry: { type: "Point", coordinates: [ll.lng, ll.lat] }, properties: {} });
}
function dragEnd(e) {
  if (!dragging) return;
  const d = dragging; dragging = null; map.dragPan.enable();
  map.getSource("drag").setData({ type: "FeatureCollection", features: [] });
  if (!d.moved || Math.hypot(e.point.x - d.from.x, e.point.y - d.from.y) < 4) return;
  suppressClick = true; setTimeout(() => { suppressClick = false; }, 80);
  enqueue(() => moveNode(d.id, e.lngLat));
}
function updateGrid() {
  const s = map.getSource("grid"); if (!s) return;
  const E = { type: "FeatureCollection", features: [] };
  if (!state.info || state.info.basemap) { s.setData(E); return; }
  const b = map.getBounds(), x0 = b.getWest() * M_LON, x1 = b.getEast() * M_LON, y0 = b.getSouth() * M_LAT, y1 = b.getNorth() * M_LAT;
  const raw = Math.max(x1 - x0, 1) / 8, p10 = Math.pow(10, Math.floor(Math.log10(raw)));
  const step = [1, 2, 5, 10].map(k => k * p10).find(v => v >= raw) || p10 * 10;
  const f = [];
  for (let x = Math.floor(x0 / step) * step; x <= x1 && f.length < 80; x += step) f.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [[x / M_LON, y0 / M_LAT], [x / M_LON, y1 / M_LAT]] } });
  for (let y = Math.floor(y0 / step) * step; y <= y1 && f.length < 160; y += step) f.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [[x0 / M_LON, y / M_LAT], [x1 / M_LON, y / M_LAT]] } });
  s.setData({ type: "FeatureCollection", features: f });
}
async function pushMap() {
  await mapReady;
  const m = state.model; if (!m) return;
  if (state.dirty.links) { map.getSource("links").setData(m.fcLinks); state.dirty.links = false; }
  if (state.dirty.nodes) { map.getSource("nodes").setData(m.fcNodes); state.dirty.nodes = false; }
  if (state.dirty.catch) { pushCatch(); state.dirty.catch = false; }
  highlight();
}
function ringOf(f) { return f.geometry.coordinates[0]; }
function centroidOf(ring) { let x = 0, y = 0; for (const p of ring) { x += p[0]; y += p[1]; } return [x / ring.length, y / ring.length]; }
function pushCatch() {
  const m = state.model, lines = [];
  for (const f of m.catchFeat) {
    const o = m.nodes.get(String(f.properties.outlet)); if (!o) continue;
    lines.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: [centroidOf(ringOf(f)), o.geometry.coordinates] } });
  }
  map.getSource("catch").setData({ type: "FeatureCollection", features: m.catchFeat });
  map.getSource("catch-links").setData({ type: "FeatureCollection", features: lines });
}
async function drawPreview() {
  await mapReady; const d = state.draw, f = [];
  if (state.catchPending) f.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[...state.catchPending, state.catchPending[0]]] } });
  else if (d && d.pts.length) {
    for (const p of d.pts) f.push({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p } });
    if (d.pts.length >= 3) f.push({ type: "Feature", properties: {}, geometry: { type: "Polygon", coordinates: [[...d.pts, d.pts[0]]] } });
    else if (d.pts.length === 2) f.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: d.pts } });
  }
  map.getSource("drawpoly").setData({ type: "FeatureCollection", features: f });
}
async function highlight() {
  await mapReady;
  const m = state.model; if (!m) return;
  const L = [], N = [];
  if (state.sel.table === "links" || state.sel.table === "catchments") for (const i of state.sel.ids) { const f = tmap(state.sel.table).get(i); if (f) L.push(f); }
  if (state.sel.table === "nodes") for (const i of state.sel.ids) { const f = m.nodes.get(i); if (f) N.push({ type: "Feature", geometry: f.geometry, properties: { _pend: 0 } }); }
  const ps = state.pipeStart && m.nodes.get(state.pipeStart);
  if (ps) N.push({ type: "Feature", geometry: ps.geometry, properties: { _pend: 1 } });
  map.getSource("sel-links").setData({ type: "FeatureCollection", features: L });
  map.getSource("sel-nodes").setData({ type: "FeatureCollection", features: N });
}
function bboxOf(coords) {
  let a = [1e9, 1e9, -1e9, -1e9];
  for (const c of coords) { a[0] = Math.min(a[0], c[0]); a[1] = Math.min(a[1], c[1]); a[2] = Math.max(a[2], c[0]); a[3] = Math.max(a[3], c[1]); }
  return a;
}
function fitModel() {
  const m = state.model; if (!m || !m.nodeFeat.length) return;
  const b = bboxOf(m.nodeFeat.map(f => f.geometry.coordinates));
  map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 50, maxZoom: 18, animate: false });
}
function zoomTo(table, ids) {
  const pts = [];
  for (const i of ids) { const f = tmap(table).get(i); if (!f) continue; if (table === "nodes") pts.push(f.geometry.coordinates); else if (table === "catchments") pts.push(...ringOf(f)); else pts.push(...f.geometry.coordinates); }
  if (!pts.length) return;
  const b = bboxOf(pts);
  if (b[0] === b[2] && b[1] === b[3]) map.jumpTo({ center: [b[0], b[1]], zoom: Math.max(map.getZoom(), 17) });
  else map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 80, maxZoom: 18, animate: false });
}

/* ------------------------------------------------------------------ data */
async function loadModel() {
  const d = await jget(`${base()}/model`);
  const nodeFeat = d.nodes.features, linkFeat = d.links.features, catchFeat = d.catchments.features;
  for (const f of catchFeat) { const r = f.geometry.coordinates[0]; if (r.length && (r[0][0] !== r[r.length - 1][0] || r[0][1] !== r[r.length - 1][1])) r.push(r[0]); }
  state.model = {
    nodeFeat, linkFeat, catchFeat, settings: d.settings, loads: d.loads,
    nodes: new Map(nodeFeat.map(f => [String(f.id), f])), links: new Map(linkFeat.map(f => [String(f.id), f])),
    catchments: new Map(catchFeat.map(f => [String(f.id), f])),
    fcNodes: { type: "FeatureCollection", features: nodeFeat }, fcLinks: { type: "FeatureCollection", features: linkFeat },
  };
  state.model.rain = d.rain || {}; syncRain();
  state.dirty.nodes = state.dirty.links = state.dirty.catch = true;
  if (state.sel.table) state.sel.ids = state.sel.ids.filter(i => tmap(state.sel.table).has(i));
  if (state.pipeStart && !state.model.nodes.has(state.pipeStart)) state.pipeStart = null;
  await mapReady;
}
/* the Rain form shows the scenario's own rain (from the model); a typed but unapplied draft survives until the rain itself changes */
function syncRain() {
  const r = state.model.rain || {}, sig = JSON.stringify(r);
  if (state.rainSig === sig) return;
  state.rainSig = sig;
  const R = { step_min: r.step_min ?? 5, duration_min: r.duration_min ?? 60, mode: "idf", idf: [], series: [] };
  if (r.idf && r.idf.durations_min) R.idf = r.idf.durations_min.map((d, i) => [d, r.idf.intensities[i]]);
  else if (Array.isArray(r.series)) { R.mode = "series"; R.series = r.series.map(x => [x[0], x[1]]); }
  state.rain = R; $("#settings-form").dataset.sig = "";
}
async function loadResults() {
  const r = await jget(`${base()}/results`);
  state.results = r; state.summary = r.summary; mergeResults();
}
function mergeResults() {
  const m = state.model, R = state.results ? state.results.links : {}; if (!m) return;
  const by = state.colorBy, S = by.startsWith("storm") ? stormNow() : null;
  if (by === "storm_q" && S) {
    const mx = Math.max(1e-9, ...Object.values(S.links).map(x => x.q_peak || 0)), cs = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#6a51a3", "#4a1486"];
    SCALES.storm_q.bins = [0.05, 0.15, 0.35, 0.6, 0.85, 1e9].map((k, i) => [k * mx, i === 5 ? `over ${+(0.85 * mx).toPrecision(3)}` : `up to ${+(k * mx).toPrecision(3)}`, cs[i]]);
  }
  for (const f of m.linkFeat) {
    const r = R[f.id], p = f.properties, sl = S && S.links[f.id];
    p._fail = r && (r.over_limit || r.over_vmax || r.surcharged || r.negative_slope) ? 1 : 0;
    p._c = by === "storm_q" ? colourFor(by, sl && sl.q_peak) : by === "storm_cap" ? colourFor(by, sl && sl.capacity_peak) : by === "storm_flood" ? GREY : colourFor(by, r && r[by]);
  }
  const wasFl = m.hasFl; let anyFl = false;
  for (const f of m.nodeFeat) {
    const fl = by === "storm_flood" && S && S.nodes[f.id] && S.nodes[f.id].flooding_peak > 0 ? 1 : 0;
    if (fl) anyFl = true; f.properties._fl = fl;
  }
  m.hasFl = anyFl; if (anyFl || wasFl) state.dirty.nodes = true;
  state.dirty.links = true;
}
const catalogueMap = () => { const o = {}; for (const [n, i] of (state.model.settings.design.catalogue || [])) o[n] = i; return o; };
function patchLocal(op) {
  const m = state.model;
  if (op.op === "set") {
    const T = tmap(op.table), cat = catalogueMap();
    for (const i of op.ids) {
      const f = T.get(String(i)); if (!f) continue; f.properties[op.field] = op.value;
      if (op.table === "links" && op.field === "dn_mm" && cat[op.value] != null) f.properties.inside_mm = cat[op.value];
    }
    if (op.table === "nodes") state.dirty.nodes = true; else state.dirty.links = true;
  } else if (op.op === "set_load") {
    (m.loads[op.set] = m.loads[op.set] || {})[op.node] = Number(op.value);
  } else if (op.op === "set_rain") {
    m.rain = JSON.parse(JSON.stringify(op.rain)); syncRain();
  } else if (op.op === "set_setting") {
    const k = op.path.split("."); let d = m.settings; for (const x of k.slice(0, -1)) d = d[x]; d[k[k.length - 1]] = op.value;
  }
}
function updateScenario(sc) {
  if (!sc) return; const i = state.info.scenarios.findIndex(s => s.id === sc.id);
  if (i >= 0) state.info.scenarios[i] = sc; else state.info.scenarios.push(sc);
}
/* one edit: post, patch or reload the model, optionally skip the re-solve fetch when more edits follow */
async function exec(op, more) {
  const r = await jpost(`${base()}/edit`, op);
  updateScenario(r.scenario); state.summary = r.summary;
  if (state.storm) state.storm.stale = true;
  if (op.op === "set_rain") state.rainApplied = true;
  if (r.structural) await loadModel(); else patchLocal(op);
  if (!more) { await loadResults(); renderAll(); }
  return r;
}
async function execMany(ops) {
  for (let k = 0; k < ops.length; k++) await exec(ops[k], k < ops.length - 1);
}
async function refreshAll(fit) {
  await Promise.all([loadModel(), loadResults().catch(e => { throw e; })]);
  mergeResults(); if (fit) { await mapReady; fitModel(); }
  renderAll();
}

/* ------------------------------------------------------------------ status, toolbar state */
function updateStatus() {
  const el = $("#status-line"), s = state.summary;
  el.dataset.rev = ++state.rev;
  if (!state.pid) { el.textContent = "No project open."; return; }
  if (!s) { el.textContent = "Solving..."; return; }
  const probs = (s.problems || []);
  el.dataset.links = s.links ?? 0; el.dataset.conduits = s.conduits ?? 0; el.dataset.problems = probs.length;
  el.dataset.seconds = s.seconds ?? "";
  if (probs.length) {
    el.innerHTML = `<span class="bad">Not solved: ${esc(probs.slice(0, 3).join("; "))}${probs.length > 3 ? ` (+${probs.length - 3} more)` : ""}</span>`;
    return;
  }
  const bad = (s.over_limit || 0) + (s.over_vmax || 0) + (s.surcharged || 0) + (s.negative_slope || 0);
  el.innerHTML = `solved ${s.links} links in ${num(s.seconds, 3)} s &middot; ${num(s.km, 2)} km &middot; over d/D limit <b class="${s.over_limit ? "bad" : ""}">${s.over_limit ?? 0}</b>` +
    ` &middot; over v max <b class="${s.over_vmax ? "bad" : ""}">${s.over_vmax ?? 0}</b> &middot; surcharged <b class="${s.surcharged ? "bad" : ""}">${s.surcharged ?? 0}</b>` +
    ` &middot; ${num(s.km_under_vmin, 2)} km under v min` + (s.negative_slope ? ` &middot; <span class="bad">${s.negative_slope} adverse</span>` : "") +
    (bad === 0 && s.links ? ` <span class="ok">&#10003;</span>` : "");
}
function updateButtons() {
  const has = !!state.pid, sc = scenario();
  for (const id of ["save-btn", "copy-btn", "tools-btn", "export-btn"]) $("#" + id).disabled = !has;
  $("#scenario-select").disabled = !has;
  $("#undo-btn").disabled = !(sc && sc.can_undo); $("#redo-btn").disabled = !(sc && sc.can_redo);
  const sel = $("#scenario-select");
  if (state.info) { sel.innerHTML = state.info.scenarios.map(s => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join(""); sel.value = state.sid; }
  $("#basemap-wrap").style.display = state.info && state.info.basemap ? "" : "none";
  $("#project-label").textContent = state.info ? `${state.info.name} - ${state.info.crs ? "EPSG:" + state.info.crs : "local metres"}` : "";
  $("#welcome").hidden = has;
  if (state.model) {
    $("#tab-nodes").textContent = `Nodes (${state.model.nodeFeat.length})`;
    $("#tab-links").textContent = `Links (${state.model.linkFeat.length})`;
  }
}
function renderAll() {
  updateStatus(); updateButtons(); pushMap(); renderProps(); renderActiveTab(); renderLegend();
}

/* ------------------------------------------------------------------ geometry hit testing */
function nearestNode(pt, tol) {
  let best = null, bd = tol; const m = state.model; if (!m) return null;
  for (const f of m.nodeFeat) {
    const p = map.project(f.geometry.coordinates), d = Math.hypot(p.x - pt.x, p.y - pt.y);
    if (d <= bd) { bd = d; best = { id: String(f.id), d }; }
  }
  return best;
}
function nearestLink(pt, tol) {
  let best = null, bd = tol; const m = state.model; if (!m) return null;
  for (const f of m.linkFeat) {
    const c = f.geometry.coordinates; let a = map.project(c[0]);
    for (let k = 1; k < c.length; k++) {
      const b = map.project(c[k]), dx = b.x - a.x, dy = b.y - a.y, L2 = dx * dx + dy * dy;
      let t = L2 ? ((pt.x - a.x) * dx + (pt.y - a.y) * dy) / L2 : 0; t = Math.max(0, Math.min(1, t));
      const px = a.x + t * dx, py = a.y + t * dy, d = Math.hypot(pt.x - px, pt.y - py);
      if (d < bd) { bd = d; best = { id: String(f.id), d, x: px, y: py }; }
      a = b;
    }
  }
  if (best) { const ll = map.unproject([best.x, best.y]); best.lng = ll.lng; best.lat = ll.lat; }
  return best;
}
function catchAt(ll) {
  const m = state.model; if (!m) return null;
  for (const f of m.catchFeat) {
    const r = ringOf(f); let inside = false;
    for (let i = 0, j = r.length - 1; i < r.length; j = i++) {
      if (((r[i][1] > ll.lat) !== (r[j][1] > ll.lat)) && (ll.lng < (r[j][0] - r[i][0]) * (ll.lat - r[i][1]) / (r[j][1] - r[i][1]) + r[i][0])) inside = !inside;
    }
    if (inside) return String(f.id);
  }
  return null;
}
/* polygon area in m2: local metres use the project's own scale; a CRS project uses the scale at the centroid */
function areaM2(pts) {
  const lat0 = pts.reduce((a, p) => a + p[1], 0) / pts.length, kx = state.info.crs ? M_LON * Math.cos(lat0 * Math.PI / 180) : M_LON, ky = state.info.crs ? 111132 : M_LAT;
  let a = 0; for (let i = 0; i < pts.length; i++) { const p = pts[i], q = pts[(i + 1) % pts.length]; a += (p[0] * kx) * (q[1] * ky) - (q[0] * kx) * (p[1] * ky); }
  return Math.abs(a) / 2;
}
function finishCatchment() {
  const d = state.draw; if (!d) return;
  const pts = d.pts.filter((p, i) => i === 0 || p[0] !== d.pts[i - 1][0] || p[1] !== d.pts[i - 1][1]);
  if (pts.length < 3) { toast("A catchment needs at least 3 corners."); return chain; }
  state.draw = null; state.catchPending = pts; drawPreview();
  $("#hint").textContent = "Now click the outlet node."; return chain;
}
function newId(table, prefix) {
  const T = tmap(table);
  for (let k = T.size + 1; ; k++) if (!T.has(prefix + k)) return prefix + k;
}

/* ------------------------------------------------------------------ tools */
const ADD_NODE = { manhole: ["manhole", "MH-"], outfall: ["outfall", "O-"], wetwell: ["wetwell", "WW-"] };
const HINTS = {
  select: "Click a node or pipe. Shift or Ctrl adds to the selection.", manhole: "Click the map to add a manhole; click on a pipe to split it.",
  outfall: "Click the map to add an outfall.", wetwell: "Click the map to add a wet well.", pipe: "Click the start node, then the end node (an empty spot makes a manhole).",
  pump: "Click the start node, then the end node.", catchment: "Click the corners; double-click or Enter to finish; then click the outlet node.", move: "Drag a node to move it.", delete: "Click a node or pipe to delete it.",
};
function setTool(t) {
  state.tool = t; state.pipeStart = null; state.movePick = null; state.draw = t === "catchment" ? { pts: [] } : null; state.catchPending = null;
  if (typeof drawPreview === "function" && map && map.getSource && map.getSource("drawpoly")) drawPreview();
  $$(".tool").forEach(b => { const on = b.id === "tool-" + t; b.classList.toggle("active", on); b.setAttribute("aria-pressed", on); });
  $("#hint").textContent = state.pid ? HINTS[t] : "";
  highlight();
}
async function act(ll, mods) {
  mods = mods || {};
  if (!state.pid || !state.model) return;
  const t = state.tool, pt = map.project(ll), lonlat = { lon: ll.lng, lat: ll.lat };
  const nn = nearestNode(pt, 12), nl = nn ? null : nearestLink(pt, 8);
  const multi = mods.shiftKey || mods.ctrlKey || mods.metaKey;
  if (t === "select") {
    if (nn) setSel("nodes", multi ? toggled("nodes", nn.id) : [nn.id]);
    else if (nl) setSel("links", multi ? toggled("links", nl.id) : [nl.id]);
    else { const c = catchAt(ll); if (c) setSel("catchments", multi ? toggled("catchments", c) : [c]); else if (!multi) setSel(null, []); }
  } else if (ADD_NODE[t]) {
    const [kind, pre] = ADD_NODE[t];
    if (nn) { setSel("nodes", [nn.id]); return; }
    if (t === "manhole" && nl) {
      const id = newId("nodes", "MH-");
      await exec({ op: "split_link", id: nl.id, lon: nl.lng, lat: nl.lat });
      setSel("nodes", [id]); return;
    }
    const id = newId("nodes", pre);
    await exec({ op: "add_node", id, kind, ...lonlat });
    setSel("nodes", [id]);
  } else if (t === "pipe" || t === "pump") {
    const kind = t === "pump" ? "pump" : "conduit";
    let endId = nn && nn.id;
    if (!state.pipeStart) {
      if (nn) { state.pipeStart = nn.id; highlight(); $("#hint").textContent = "Now click the end node."; }
      else toast("Click a start node first.");
      return;
    }
    if (nn && nn.id === state.pipeStart) return;
    if (!endId) { endId = newId("nodes", "MH-"); await exec({ op: "add_node", id: endId, kind: "manhole", ...lonlat }, true); }
    const id = newId("links", kind === "pump" ? "PMP-" : "P-");
    const from = state.pipeStart; state.pipeStart = null;
    await exec({ op: "add_link", id, kind, from_node: from, to_node: endId, dn_mm: state.info.catalogue[0] });
    setSel("links", [id]); $("#hint").textContent = HINTS[t];
  } else if (t === "catchment") {
    if (state.catchPending) {
      if (!nn) { toast("Click the outlet node."); return; }
      const pts = state.catchPending, m2 = areaM2(pts), id = newId("catchments", "CM-");
      state.catchPending = null; state.draw = { pts: [] }; drawPreview();
      await exec({ op: "add_catchment", id, outlet: nn.id, area_ha: m2 / 1e4, imperv_pc: 50, width_m: Math.sqrt(m2), slope_pc: 1, coords_ll: pts });
      setSel("catchments", [id]); $("#hint").textContent = HINTS.catchment;
    } else { state.draw = state.draw || { pts: [] }; state.draw.pts.push([ll.lng, ll.lat]); drawPreview(); }
  } else if (t === "delete") {
    if (nn) await deleteIds("nodes", [nn.id]); else if (nl) await deleteIds("links", [nl.id]);
    else { const c = catchAt(ll); if (c) await deleteIds("catchments", [c]); }
  } else if (t === "move") {
    if (!state.movePick) { if (nn) { state.movePick = nn.id; setSel("nodes", [nn.id]); $("#hint").textContent = "Click the new position."; } }
    else { const id = state.movePick; state.movePick = null; $("#hint").textContent = HINTS.move; await moveNode(id, ll); }
  }
}
async function moveNode(id, ll) { await exec({ op: "move_node", id, lon: ll.lng, lat: ll.lat }); }
async function deleteIds(table, ids) {
  if (state.sel.table === table) state.sel.ids = state.sel.ids.filter(i => !ids.includes(i));
  await exec({ op: "delete", table, ids });
}
function toggled(table, id) {
  const cur = state.sel.table === table ? state.sel.ids.slice() : [];
  const k = cur.indexOf(id); if (k >= 0) cur.splice(k, 1); else cur.push(id); return cur;
}
function setSel(table, ids, opt) {
  opt = opt || {};
  state.sel = { table: ids.length ? table : null, ids: ids.slice() };
  highlight(); renderProps(); renderActiveTab();
  if (opt.zoom && ids.length) zoomTo(table, ids);
  if (state.tab === "profile") autoProfile();
  if (state.tab === "hydro") drawHydro();
}

/* ------------------------------------------------------------------ property grid */
const RO = new Set(["id", "x", "y", "from_node", "to_node", "inside_mm", "outlet"]);
const UNITS = { area_ha: "ha", imperv_pc: "%", width_m: "m", slope_pc: "%", x: "m", y: "m", ground: "m", invert: "m", inflow_m3d: "m3/d", length_m: "m", dn_mm: "mm", inside_mm: "mm", up_inv: "m", dn_inv: "m" };
const NUMF = new Set(["area_ha", "imperv_pc", "width_m", "slope_pc", "n_imperv", "n_perv", "x", "y", "ground", "invert", "inflow_m3d", "length_m", "up_inv", "dn_inv", "inside_mm"]);
let gridSig = "";
function fieldType(table, k, v) {
  if (RO.has(k)) return "ro";
  if (k === "kind") return "kind"; if (k === "dn_mm") return "dn"; if (k === "transfer") return "bool";
  if (NUMF.has(k) || typeof v === "number") return "num";
  return "ro";
}
function selFeatures() {
  const m = state.model; if (!m || !state.sel.table) return [];
  const T = tmap(state.sel.table); return state.sel.ids.map(i => T.get(i)).filter(Boolean);
}
function renderProps() {
  const host = $("#prop-grid"), fs = selFeatures();
  if (!fs.length) { host.innerHTML = `<p class="muted">Nothing selected. Use the Select tool, or click a row in a table.</p>`; gridSig = ""; return; }
  const table = state.sel.table, keys = Object.keys(fs[0].properties).filter(k => !k.startsWith("_"));
  const multi = fs.length > 1, sig = [table, state.sel.ids.join(","), keys.join(",")].join("|");
  const focusedField = document.activeElement && host.contains(document.activeElement) ? document.activeElement.dataset.field : null;
  const val = k => { const v0 = fs[0].properties[k]; return fs.every(f => f.properties[k] === v0) ? v0 : undefined; };
  if (sig === gridSig && focusedField != null) {          // same selection and the user is typing: update the other controls in place
    for (const inp of $$("[data-field]", host)) { if (inp.dataset.field === focusedField || inp.dataset.kind === "load") continue; const v = val(inp.dataset.field); if (v !== undefined) inp.type === "checkbox" ? (inp.checked = !!v) : (inp.value = v == null ? "" : v); }
    renderResultsBlock(); return;
  }
  gridSig = sig;
  const head = multi ? `${fs.length} ${table}` : `${{ nodes: "Node", links: "Link", catchments: "Catchment" }[table]} ${esc(fs[0].properties.id)}`;
  let h = `<h4 data-testid="prop-title">${head}</h4>`;
  for (const k of keys) {
    if (multi && ["id", "x", "y", "from_node", "to_node"].includes(k)) continue;
    const v = val(k), ty = fieldType(table, k, fs[0].properties[k]);
    h += `<div class="pr"><label for="prop-${k}">${esc(k)}</label>${control(table, k, ty, v)}<span class="u">${UNITS[k] || ""}</span></div>`;
  }
  if (table === "nodes") {
    const sets = Object.keys(state.model.loads || {});
    h += `<h5>Load (m3/d) per load set</h5>`;
    for (const s of sets) {
      const vals = fs.map(f => (state.model.loads[s] || {})[f.id] ?? 0), v = vals.every(x => x === vals[0]) ? vals[0] : "";
      h += `<div class="pr"><label>${esc(s)}</label><input type="number" step="any" id="load-${esc(s)}" data-testid="load-${esc(s)}" data-kind="load" data-set="${esc(s)}" value="${v}"><span class="u">m3/d</span></div>`;
    }
  }
  h += `<div id="res-block"></div>`;
  host.innerHTML = h; tag(host);
  $$("[data-field]", host).forEach(inp => {
    const field = inp.dataset.field, ty = inp.dataset.type;
    const go = () => {
      if (inp.dataset.kind === "load") return;
      let v = inp.type === "checkbox" ? inp.checked : inp.value;
      if (ty === "num" || ty === "dn") { if (v === "") return; v = Number(v); if (!isFinite(v)) return; }
      const cur = val(field); if (cur !== undefined && cur === v) return;
      if (inp._sent === v) return; inp._sent = v;
      const ids = state.sel.ids.slice(), tb = state.sel.table;
      enqueue(() => setField(tb, ids, field, v));
    };
    inp.addEventListener("focus", () => { inp._sent = undefined; });
    inp.addEventListener("change", go);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { go(); inp.blur && inp.blur(); } });
  });
  $$("[data-kind=load]", host).forEach(inp => {
    const go = () => { if (inp.value === "" || inp._sent === inp.value) return; inp._sent = inp.value; const v = Number(inp.value), set = inp.dataset.set, ids = state.sel.ids.slice(); enqueue(() => execMany(ids.map((n, k) => ({ op: "set_load", set, node: n, value: v })))); };
    inp.addEventListener("focus", () => { inp._sent = undefined; });
    inp.addEventListener("change", go);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { go(); inp.blur(); } });
  });
  renderResultsBlock();
}
function control(table, k, ty, v) {
  const a = `id="prop-${k}" data-testid="prop-${k}" data-field="${k}" data-type="${ty}"`, vs = v === undefined ? "" : esc(v ?? "");
  const ph = v === undefined ? ` placeholder="mixed"` : "";
  if (ty === "ro") return `<input type="text" ${a} value="${vs}"${ph} readonly>`;
  if (ty === "kind") {
    const kinds = table === "nodes" ? state.info.node_kinds : state.info.link_kinds;
    return `<select ${a}>${v === undefined ? `<option value="" selected>mixed</option>` : ""}${kinds.map(o => `<option${o === v ? " selected" : ""}>${o}</option>`).join("")}</select>`;
  }
  if (ty === "dn") return `<select ${a}>${v === undefined ? `<option value="" selected>mixed</option>` : ""}${state.info.catalogue.map(o => `<option${o === v ? " selected" : ""}>${o}</option>`).join("")}</select>`;
  if (ty === "bool") return `<input type="checkbox" ${a} ${v ? "checked" : ""}>`;
  return `<input type="number" step="any" ${a} value="${vs}"${ph}>`;
}
function renderResultsBlock() {
  const host = $("#res-block"); if (!host) return;
  const R = state.results ? state.results.links : {};
  if (state.sel.table !== "links" || state.sel.ids.length !== 1) { host.innerHTML = ""; return; }
  const r = R[state.sel.ids[0]];
  if (!r) { host.innerHTML = `<h5>Results</h5><p class="muted">No result (the network could not be solved, or this is a pump).</p>`; return; }
  const rows = [["q_ls", "Flow (L/s)"], ["v_ms", "Velocity (m/s)"], ["d_over_D", "d/D"], ["limit", "d/D limit"], ["s_pc", "Slope (%)"]];
  let h = `<h5>Results (read-only)</h5>`;
  for (const [k, l] of rows) h += `<div class="pr"><label>${l}</label><span data-testid="res-${k}">${num(r[k], 4)}</span><span></span></div>`;
  const fl = ["over_limit", "over_vmax", "surcharged", "negative_slope", "under_vmin"].filter(k => r[k]);
  h += `<div class="pr"><label>Flags</label><span class="${fl.length ? "flag" : ""}" data-testid="res-flags">${fl.length ? fl.join(", ") : "none"}</span><span></span></div>`;
  host.innerHTML = h;
}
async function setField(table, ids, field, value) {
  // the server moves link end inverts that sat at the node's old invert, in the same undoable edit
  await execMany([{ op: "set", table, ids, field, value }]);
}

/* ------------------------------------------------------------------ flex tables */
const NODE_COLS = ["id", "kind", "x", "y", "ground", "invert", "inflow_m3d", "load"];
const LINK_COLS = ["id", "kind", "from_node", "to_node", "length_m", "dn_mm", "inside_mm", "up_inv", "dn_inv", "transfer"];
const RES_COLS = ["id", "dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc", "flags"];
const TOOL_COLS = ["id", "dn_mm", "q_ls", "v_ms", "d_over_D", "limit", "s_pc", "flags"];
const BULK_NODES = ["ground", "invert", "inflow_m3d", "kind"], BULK_LINKS = ["dn_mm", "kind", "length_m", "up_inv", "dn_inv", "transfer"];
const FLAGS = { over_limit: "d/D limit", over_vmax: "v max", surcharged: "surcharged", negative_slope: "adverse", under_vmin: "v min" };
function flagText(r) { return Object.keys(FLAGS).filter(k => r && r[k]).map(k => FLAGS[k]).join(", "); }
function rowsFor(kind) {
  const m = state.model; if (!m) return [];
  const R = state.results ? state.results.links : {};
  if (kind === "nodes") { const ls = m.loads[m.settings.design_load] || {}; return m.nodeFeat.map(f => ({ ...f.properties, load: ls[f.id] ?? 0 })); }
  if (kind === "links") return m.linkFeat.map(f => f.properties);
  if (kind === "results") return m.linkFeat.filter(f => R[f.id]).map(f => ({ id: String(f.id), ...R[f.id], flags: flagText(R[f.id]) }));
  if (kind === "toolout") return (state.toolout && state.toolout.rows || []).map(r => ({ ...r, flags: flagText(r) }));
  return [];
}
function colsOf(kind) { return kind === "toolout" && state.toolout && state.toolout.cols ? state.toolout.cols : { nodes: NODE_COLS, links: LINK_COLS, results: RES_COLS, toolout: TOOL_COLS }[kind]; }
function renderTable(kind) {
  const st = state.table[kind], tbl = $("#tbl-" + kind); if (!tbl) return;
  let rows = rowsFor(kind);
  const q = st.filter.trim().toLowerCase();
  if (q) rows = rows.filter(r => Object.values(r).join(" ").toLowerCase().includes(q));
  const k = st.sort, d = st.dir;
  rows.sort((a, b) => {
    const x = a[k], y = b[k]; if (x === y) return 0; if (x == null) return 1; if (y == null) return -1;
    return (typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y), undefined, { numeric: true })) * d;
  });
  state.view[kind] = rows.map(r => String(r.id));
  const pages = Math.max(1, Math.ceil(rows.length / PAGE)); st.page = Math.min(st.page, pages - 1);
  const slice = rows.slice(st.page * PAGE, st.page * PAGE + PAGE);
  const selTable = kind === "results" || kind === "toolout" ? "links" : kind;
  const sel = new Set(state.sel.table === selTable ? state.sel.ids : []);
  const cols = colsOf(kind);
  tbl.innerHTML = `<thead><tr>${cols.map(c => `<th data-col="${c}" class="${c === k ? "sorted" + (d < 0 ? " desc" : "") : ""}">${c}</th>`).join("")}</tr></thead><tbody>` +
    slice.map(r => `<tr data-id="${esc(r.id)}" class="${sel.has(String(r.id)) ? "sel" : ""}">${cols.map(c => {
      const v = r[c]; return `<td class="${c === "flags" ? "flag" : ""}">${esc(typeof v === "number" ? +v.toFixed(4) : v)}</td>`;
    }).join("")}</tr>`).join("") + `</tbody>`;
  const cnt = $("#count-" + kind);
  if (cnt) cnt.innerHTML = `${rows.length} rows` + (pages > 1 ? ` &middot; <span class="pager"><button class="tb" data-pg="-1">&lsaquo;</button> page ${st.page + 1} of ${pages} <button class="tb" data-pg="1">&rsaquo;</button></span>` : "") + (sel.size ? ` &middot; ${sel.size} selected` : "");
  tag(tbl);
  updateBulk(kind);
}
function initTables() {
  for (const kind of ["nodes", "links", "results", "toolout"]) {
    const tbl = $("#tbl-" + kind), st = state.table[kind];
    tbl.addEventListener("click", e => {
      const th = e.target.closest("th[data-col]");
      if (th) { const c = th.dataset.col; if (st.sort === c) st.dir *= -1; else { st.sort = c; st.dir = 1; } renderTable(kind); return; }
      const tr = e.target.closest("tr[data-id]"); if (!tr) return;
      const id = tr.dataset.id, table = kind === "results" || kind === "toolout" ? "links" : kind;
      if (e.ctrlKey || e.metaKey) { setSel(table, toggled(table, id)); state.anchor[kind] = id; }
      else if (e.shiftKey && state.anchor[kind]) {
        const v = state.view[kind], a = v.indexOf(state.anchor[kind]), b = v.indexOf(id);
        if (a >= 0 && b >= 0) setSel(table, v.slice(Math.min(a, b), Math.max(a, b) + 1)); else setSel(table, [id]);
      } else { state.anchor[kind] = id; setSel(table, [id], { zoom: true }); }
    });
    const f = $("#filter-" + kind); if (f) f.addEventListener("input", () => { st.filter = f.value; st.page = 0; renderTable(kind); });
    const cnt = $("#count-" + kind); if (cnt) cnt.addEventListener("click", e => { const b = e.target.closest("[data-pg]"); if (b) { st.page = Math.max(0, st.page + Number(b.dataset.pg)); renderTable(kind); } });
  }
  for (const kind of ["nodes", "links"]) {
    const fsel = $("#bulk-field-" + kind), fields = kind === "nodes" ? BULK_NODES : BULK_LINKS;
    fsel.innerHTML = fields.map(f => `<option>${f}</option>`).join("");
    fsel.addEventListener("change", () => bulkControl(kind));
    $("#bulk-apply-" + kind).addEventListener("click", () => {
      if (state.sel.table !== kind || !state.sel.ids.length) { toast("Select rows first (Ctrl or Shift for several)."); return; }
      const field = fsel.value, c = $("#bulk-value-" + kind); let v = c.type === "checkbox" ? c.checked : c.value;
      if (c.dataset.type === "num") { if (v === "") return; v = Number(v); }
      else if (field === "transfer") v = v === "true";
      const ids = state.sel.ids.slice();
      enqueue(() => setField(kind, ids, field, v));
    });
    bulkControl(kind);
  }
}
function bulkControl(kind) {
  const field = $("#bulk-field-" + kind).value, host = $("#bulk-val-" + kind); let h;
  const a = `id="bulk-value-${kind}" data-testid="bulk-value-${kind}"`;
  if (field === "dn_mm") h = `<select ${a} data-type="num">${(state.info ? state.info.catalogue : []).map(o => `<option>${o}</option>`).join("")}</select>`;
  else if (field === "kind") h = `<select ${a}>${((state.info ? (kind === "nodes" ? state.info.node_kinds : state.info.link_kinds) : [])).map(o => `<option>${o}</option>`).join("")}</select>`;
  else if (field === "transfer") h = `<select ${a}><option>true</option><option>false</option></select>`;
  else h = `<input type="number" step="any" ${a} data-type="num" style="width:90px">`;
  host.innerHTML = h;
}
function updateBulk(kind) {
  if (kind !== "nodes" && kind !== "links") return;
  const sel = $("#bulk-field-" + kind); if (state.info && !sel.dataset.catSig) { sel.dataset.catSig = "1"; }
  const c = $("#bulk-value-" + kind);
  if (c && c.tagName === "SELECT" && $("#bulk-field-" + kind).value === "dn_mm" && state.info && c.options.length !== state.info.catalogue.length) bulkControl(kind);
}

/* ------------------------------------------------------------------ profile */
let profSeq = 0;
function autoProfile() {
  const m = state.model; if (!m) return;
  let start = "";
  if (state.sel.table === "nodes" && state.sel.ids.length) start = state.sel.ids[0];
  else if (state.sel.table === "links" && state.sel.ids.length) { const f = m.links.get(state.sel.ids[0]); if (f) start = f.properties.from_node; }
  if (start) $("#prof-start").value = start;
  drawProfile();
}
async function drawProfile() {
  const start = $("#prof-start").value.trim(), end = $("#prof-end").value.trim(), msg = $("#prof-msg"), svg = $("#profile-svg");
  if (!state.pid) return;
  if (!start) { msg.textContent = "Select a node or a pipe, or type a start node."; svg.innerHTML = ""; return; }
  const seq = ++profSeq;
  try {
    const rows = await jget(`${base()}/profile?start=${encodeURIComponent(start)}` + (end ? `&end=${encodeURIComponent(end)}` : ""));
    if (seq !== profSeq) return;
    msg.textContent = `${rows.length} links from ${start}`;
    renderProfile(rows);
  } catch (e) { if (seq !== profSeq) return; msg.textContent = e.message; svg.innerHTML = ""; }
}
function niceStep(span, n) { const raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))); return ([1, 2, 5, 10].map(k => k * p).find(v => v >= raw)) || p * 10; }
function renderProfile(rows) {
  const svg = $("#profile-svg"), wrap = $("#prof-wrap");
  const W = Math.max(520, wrap.clientWidth - 16), H = Math.max(190, wrap.clientHeight - 6);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  if (!rows.length) { svg.innerHTML = `<text x="20" y="30">No links.</text>`; return; }
  const L = 58, R = 18, T = 26, B = 66, pw = W - L - R, ph = H - T - B;
  const xmax = rows[rows.length - 1].ch1 || 1;
  let lo = 1e9, hi = -1e9;
  for (const r of rows) for (const v of [r.ground0, r.ground1, r.inv0, r.inv1, r.crown0, r.crown1]) if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const pad = Math.max((hi - lo) * 0.06, 0.2); lo -= pad; hi += pad;
  const X = c => L + c / xmax * pw, Y = v => T + (hi - v) / (hi - lo) * ph;
  let s = `<rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="#fafbfc" stroke="#d5dbe3"/>`;
  const sx = niceStep(xmax, Math.max(2, pw / 90)), sy = niceStep(hi - lo, Math.max(2, ph / 36));
  for (let c = 0; c <= xmax + 1e-9; c += sx) s += `<line x1="${X(c)}" x2="${X(c)}" y1="${T}" y2="${T + ph}" stroke="#eef1f5"/><text x="${X(c)}" y="${T + ph + 14}" text-anchor="middle">${+c.toFixed(1)}</text>`;
  for (let v = Math.ceil(lo / sy) * sy; v <= hi; v += sy) s += `<line x1="${L}" x2="${L + pw}" y1="${Y(v)}" y2="${Y(v)}" stroke="#eef1f5"/><text x="${L - 6}" y="${Y(v) + 3}" text-anchor="end">${+v.toFixed(2)}</text>`;
  s += `<text x="${L + pw / 2}" y="${T + ph + 30}" text-anchor="middle">Chainage (m)</text><text transform="translate(14 ${T + ph / 2}) rotate(-90)" text-anchor="middle">Level (m)</text>`;
  // ground
  const g = [[0, rows[0].ground0]]; for (const r of rows) g.push([r.ch1, r.ground1]);
  s += `<polyline points="${g.map(p => `${X(p[0])},${Y(p[1])}`).join(" ")}" fill="none" stroke="#8a6d3b" stroke-width="2"/>`;
  // links
  for (const r of rows) {
    const x0 = X(r.ch0), x1 = X(r.ch1), tip = `${r.link}  DN${r.dn_mm}  v ${r.v_ms == null ? "-" : (+r.v_ms).toFixed(2)} m/s`;
    s += `<g class="seg" data-link="${esc(r.link)}"><title>${esc(tip)}</title>` +
      `<polygon points="${x0},${Y(r.inv0)} ${x1},${Y(r.inv1)} ${x1},${Y(r.crown1)} ${x0},${Y(r.crown0)}" fill="#cfe0f5" fill-opacity=".7" stroke="none"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.inv0)}" x2="${x1}" y2="${Y(r.inv1)}" stroke="#1f3b73" stroke-width="1.6"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.crown0)}" x2="${x1}" y2="${Y(r.crown1)}" stroke="#4c78b8" stroke-width="1.6"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.water0)}" x2="${x1}" y2="${Y(r.water1)}" stroke="#2a9df4" stroke-width="1.6"/></g>`;
    if (x1 - x0 > 70) s += `<text x="${(x0 + x1) / 2}" y="${Y((r.inv0 + r.inv1) / 2) + 14}" text-anchor="middle">DN${r.dn_mm}</text>`;
  }
  // node shafts and labels
  const nodes = [[rows[0].from_node, 0, rows[0].ground0, rows[0].inv0]]; for (const r of rows) nodes.push([r.to_node, r.ch1, r.ground1, r.inv1]);
  let lastX = -99;
  for (const [id, c, gr, iv] of nodes) {
    s += `<line x1="${X(c)}" x2="${X(c)}" y1="${Y(gr)}" y2="${Y(iv)}" stroke="#7a8696" stroke-dasharray="3 2"/>`;
    if (X(c) - lastX > 16) { s += `<text transform="translate(${X(c) + 3} ${Y(gr) - 5}) rotate(-60)">${esc(id)}</text>`; lastX = X(c); }
  }
  // legend under the axis
  const lg = [["#8a6d3b", "Ground"], ["#1f3b73", "Invert"], ["#4c78b8", "Crown"], ["#2a9df4", "Water surface"]]; let lx = L;
  for (const [c, t] of lg) { s += `<line x1="${lx}" x2="${lx + 18}" y1="${H - 10}" y2="${H - 10}" stroke="${c}" stroke-width="2.4"/><text x="${lx + 24}" y="${H - 6}">${t}</text>`; lx += 24 + t.length * 6.2 + 22; }
  svg.innerHTML = s;
}

/* ------------------------------------------------------------------ hydrograph (after a storm run) */
const HYDRO = { link: [["flow_rate", "Flow rate"], ["flow_depth", "Flow depth"]], node: [["invert_depth", "Depth above invert"]], subcatch: [["runoff_rate", "Runoff rate"]] };
let hydroSeq = 0;
async function drawHydro() {
  const svg = $("#hydro-svg"), msg = $("#hydro-msg"), sel = $("#hydro-attr");
  if (!state.pid) return;
  const kind = { links: "link", nodes: "node", catchments: "subcatch" }[state.sel.table], id = state.sel.ids[0];
  if (!kind) { svg.innerHTML = ""; msg.textContent = "Select a link, node or catchment."; return; }
  if (!stormNow()) { svg.innerHTML = ""; msg.textContent = "Run Tools > Run on EPA SWMM first."; return; }
  if (!sel.dataset.kind || sel.dataset.kind !== kind) { sel.innerHTML = HYDRO[kind].map(a => `<option value="${a[0]}">${a[1]}</option>`).join(""); sel.dataset.kind = kind; }
  const attr = sel.value, seq = ++hydroSeq;
  try {
    const r = await jget(`${base()}/storm/series?kind=${kind}&id=${encodeURIComponent(id)}&attr=${attr}`);
    if (seq !== hydroSeq) return;
    msg.textContent = `${kind} ${id}`; $("#hydro-title").textContent = `${HYDRO[kind].find(a => a[0] === attr)[1]} of ${id}`;
    renderHydro(r.series, HYDRO[kind].find(a => a[0] === attr)[1]);
  } catch (e) { if (seq !== hydroSeq) return; svg.innerHTML = ""; msg.textContent = e.message; }
}
function renderHydro(ser, label) {
  const svg = $("#hydro-svg"), wrap = $("#hydro-wrap"), W = Math.max(520, wrap.clientWidth - 16), H = Math.max(190, wrap.clientHeight - 6);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  if (!ser.length) { svg.innerHTML = `<text x="20" y="30">No data.</text>`; return; }
  const L = 60, R = 18, T = 14, B = 44, pw = W - L - R, ph = H - T - B;
  const xs = ser.map(p => p[0] / 3600), ys = ser.map(p => p[1]), xmax = Math.max(...xs, 1e-9), ymax = Math.max(...ys, 1e-9) * 1.08, ymin = Math.min(0, ...ys);
  const X = v => L + v / xmax * pw, Y = v => T + (ymax - v) / (ymax - ymin) * ph;
  let s = `<rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="#fafbfc" stroke="#d5dbe3"/>`;
  const sx = niceStep(xmax, Math.max(2, pw / 80)), sy = niceStep(ymax - ymin, Math.max(2, ph / 36));
  for (let c = 0; c <= xmax + 1e-9; c += sx) s += `<line x1="${X(c)}" x2="${X(c)}" y1="${T}" y2="${T + ph}" stroke="#eef1f5"/><text x="${X(c)}" y="${T + ph + 14}" text-anchor="middle">${+c.toFixed(2)}</text>`;
  for (let v = Math.ceil(ymin / sy) * sy; v <= ymax; v += sy) s += `<line x1="${L}" x2="${L + pw}" y1="${Y(v)}" y2="${Y(v)}" stroke="#eef1f5"/><text x="${L - 6}" y="${Y(v) + 3}" text-anchor="end">${+v.toPrecision(3)}</text>`;
  s += `<text x="${L + pw / 2}" y="${H - 6}" text-anchor="middle">Time (h)</text><text transform="translate(14 ${T + ph / 2}) rotate(-90)" text-anchor="middle">${esc(label)}</text>`;
  s += `<polyline class="curve" points="${xs.map((x, i) => `${X(x).toFixed(1)},${Y(ys[i]).toFixed(1)}`).join(" ")}" fill="none" stroke="#1f6feb" stroke-width="2"/>`;
  svg.innerHTML = s;
}

/* ------------------------------------------------------------------ settings */
function renderSettings() {
  const m = state.model, host = $("#settings-form"); if (!m) { host.innerHTML = `<p class="muted">No project open.</p>`; return; }
  if (host.contains(document.activeElement) && host.dataset.sig === state.pid + state.sid) return;
  const S = m.settings, sets = Object.keys(m.loads || {});
  const get = p => p.split(".").reduce((o, k) => (o == null ? o : o[k]), S);
  const row = (path, label, type, opts) => {
    const v = get(path), a = `id="set-${path}" data-testid="set-${path}" data-path="${path}" data-type="${type}"`;
    let c;
    if (type === "select") c = `<select ${a}>${opts.map(o => `<option value="${o[0]}"${String(o[0]) === String(v ?? "") ? " selected" : ""}>${o[1]}</option>`).join("")}</select>`;
    else c = `<input type="number" step="any" ${a} value="${v ?? ""}">`;
    return `<div class="sr"><label for="set-${path}">${label}</label>${c}</div>`;
  };
  const loadOpts = sets.map(s => [s, s]);
  host.innerHTML =
    `<fieldset><legend>Friction</legend>${row("friction.method", "Method", "select", [["colebrook", "Colebrook-White"], ["manning", "Manning"]])}${row("friction.ks_mm", "ks (mm)", "num")}${row("friction.manning_n", "Manning n", "num")}</fieldset>` +
    `<fieldset><legend>Peaking</legend>${row("peaking.method", "Method", "select", ["table", "peltier", "merrimack", "constant", "none"].map(x => [x, x]))}${row("peaking.constant", "Constant factor", "num")}</fieldset>` +
    `<fieldset><legend>Flows</legend>${row("infiltration_m3d_per_km", "Infiltration (m3/d/km)", "num")}${row("design_load", "Design load set", "select", loadOpts)}${row("check_load", "Check load set", "select", [["", "(none)"], ...loadOpts])}</fieldset>` +
    `<fieldset><legend>Design limits</legend>${row("design.v_min", "v min (m/s)", "num")}${row("design.v_max", "v max (m/s)", "num")}${row("design.cover_min", "Cover min (m)", "num")}${row("design.cover_max", "Cover max (m)", "num")}</fieldset>`;
  host.insertAdjacentHTML("beforeend", rainHtml());
  host.dataset.sig = state.pid + state.sid; tag(host);
  $$("[data-path]", host).forEach(inp => inp.addEventListener("change", () => {
    let v = inp.value; if (inp.dataset.type === "num") { if (v === "") return; v = Number(v); }
    if (inp.dataset.path === "check_load" && v === "") v = null;
    const path = inp.dataset.path; enqueue(() => exec({ op: "set_setting", path, value: v }));
  }));
  wireRain(host);
}
/* rain: an IDF table (duration, intensity) or a time series (minute, intensity); applied as one set_rain edit */
function rainHtml() {
  const R = state.rain, rows = R.mode === "idf" ? R.idf : R.series, la = R.mode === "idf" ? "Duration (min)" : "Minute", lb = "Intensity (mm/h)";
  return `<fieldset class="wide" id="rain-box"><legend>Rain</legend><div class="rain-top" style="display:flex;gap:18px;flex-wrap:wrap;align-items:end">` +
    `<label>Step (min)<br><input type="number" step="any" id="rain-step" value="${R.step_min}" style="width:90px"></label>` +
    `<label>Duration (min)<br><input type="number" step="any" id="rain-duration" value="${R.duration_min}" style="width:90px"></label>` +
    `<label>Defined by<br><select id="rain-mode" style="width:150px"><option value="idf"${R.mode === "idf" ? " selected" : ""}>IDF table</option><option value="series"${R.mode === "series" ? " selected" : ""}>Time series</option></select></label>` +
    `<button id="rain-apply" class="tb2">Apply rain</button><span id="rain-msg" class="muted"></span></div>` +
    `<div style="margin-top:8px"><div class="rr muted"><span>${la}</span><span>${lb}</span><span></span></div>` +
    rows.map((r, i) => `<div class="rr"><input type="number" step="any" id="rain-row-${i}-a" data-i="${i}" data-c="0" value="${r[0] ?? ""}"><input type="number" step="any" id="rain-row-${i}-b" data-i="${i}" data-c="1" value="${r[1] ?? ""}"><button id="rain-del-${i}" data-del="${i}" title="Remove row">&times;</button></div>`).join("") +
    `<button id="rain-add-row" class="tb2">Add row</button></div></fieldset>`;
}
function wireRain(host) {
  const R = state.rain, rows = () => R.mode === "idf" ? R.idf : R.series;
  const rerender = () => { host.dataset.sig = ""; renderSettings(); };
  $("#rain-step").onchange = e => { R.step_min = Number(e.target.value); };
  $("#rain-duration").onchange = e => { R.duration_min = Number(e.target.value); };
  $("#rain-mode").onchange = e => { R.mode = e.target.value; rerender(); };
  $("#rain-add-row").onclick = () => { rows().push(["", ""]); rerender(); };
  $$("[data-i]", host).forEach(inp => inp.addEventListener("input", () => { rows()[+inp.dataset.i][+inp.dataset.c] = inp.value === "" ? "" : Number(inp.value); }));
  $$("[data-del]", host).forEach(b => b.onclick = () => { rows().splice(+b.dataset.del, 1); rerender(); });
  $("#rain-apply").onclick = () => {
    R.step_min = Number($("#rain-step").value); R.duration_min = Number($("#rain-duration").value);
    const rs = rows().filter(r => r[0] !== "" && r[1] !== "");
    if (!rs.length) { $("#rain-msg").textContent = "Add at least one row."; return; }
    let rain;
    if (R.mode === "idf") { const s = rs.slice().sort((a, b) => a[0] - b[0]); rain = { step_min: R.step_min, duration_min: R.duration_min, idf: { durations_min: s.map(r => r[0]), intensities: s.map(r => r[1]) } }; }
    else rain = { step_min: R.step_min, series: rs.slice().sort((a, b) => a[0] - b[0]) };
    $("#rain-msg").textContent = "";
    enqueue(() => exec({ op: "set_rain", rain }));
  };
}

/* ------------------------------------------------------------------ tools menu and tool output */
async function loadToolList() {
  try { state.tools = await jget("/tools"); } catch (e) { state.tools = []; }
  const host = $("#tools-menu"), groups = {};
  for (const t of state.tools.filter(t => t.name !== "assistant")) (groups[t.menu || "Tools"] = groups[t.menu || "Tools"] || []).push(t);
  host.innerHTML = Object.entries(groups).map(([g, ts]) => `<div class="mh">${esc(g)}</div>` +
    ts.map(t => `<button data-tool="${esc(t.name)}" data-testid="tool-run-${esc(t.name)}" title="${esc(t.label)}">${esc(t.label.split(/[:(]/)[0].trim())}</button>`).join("")).join("");
  $$("button", host).forEach(b => b.addEventListener("click", () => { host.hidden = true; const t = state.tools.find(x => x.name === b.dataset.tool); enqueue(() => runTool(t)); }));
}
async function runTool(t) {
  if (!state.pid) return;
  const [method, path0] = t.endpoint.split(/\s+/);
  const path = path0.replace(/^\/api\/g/, "").replace("{pid}", state.pid).replace("{sid}", state.sid);
  busy(true, `${t.label.split(/[:(]/)[0].trim()}...`);
  try {
    const resp = await api(path, method === "POST" ? { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" } : undefined);
    if (!/json/.test(resp.headers.get("content-type") || "")) { await saveBlob(resp, "model.inp"); return; }
    const r = await resp.json();
    if (r.subcatchments) {                                   // a storm run: its summary is SWMM's, not the steady solver's
      state.storm = { sid: state.sid, data: r, stale: false };
      const rows = Object.entries(r.links).map(([id, v]) => ({ id, ...v })).sort((a, b) => (b.capacity_peak || 0) - (a.capacity_peak || 0));
      state.toolout = { tool: t, rows, cols: ["id", "q_peak", "v_peak", "depth_peak", "capacity_peak"], report: { ...r.summary, seconds: r.seconds }, storm: true };
      state.colorBy = "storm_cap"; $("#color-by").value = "storm_cap"; mergeResults();
    } else {
      state.toolout = { tool: t, rows: r.rows || [], report: r.report || null, summary: r.summary };
      if (r.scenario) updateScenario(r.scenario);
      if (r.summary) state.summary = r.summary;
      if (r.structural) await loadModel();
      await loadResults();
    }
    showTab("toolout"); renderAll();
  } finally { busy(false); }
}
async function saveBlob(resp, fallback) {
  const cd = resp.headers.get("content-disposition") || "", mt = /filename="?([^";]+)"?/.exec(cd), blob = await resp.blob();
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = mt ? mt[1] : fallback;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
function renderToolOut() {
  const o = state.toolout, title = $("#toolout-title"), rep = $("#toolout-report");
  if (!o) { title.textContent = "No tool run yet. Use the Tools menu."; rep.innerHTML = ""; $("#tbl-toolout").innerHTML = ""; return; }
  title.textContent = o.tool.label;
  let h = "";
  if (o.report) {
    const r = o.report, flat = [];
    const walk = (obj, pre) => { for (const [k, v] of Object.entries(obj)) { if (k === "sizes") continue; if (v && typeof v === "object" && !Array.isArray(v)) walk(v, pre + k + "."); else flat.push([pre + k, v]); } };
    walk(r, "");
    h += `<div class="kv" data-testid="${o.storm ? "storm-report" : "design-report"}">` + flat.map(([k, v]) => `<span>${esc(k.replace(/_/g, " "))}: <b data-k="${esc(k)}">${esc(typeof v === "number" ? +v.toFixed(4) : Array.isArray(v) ? v.join(", ") : v)}</b></span>`).join("") + `</div>`;
    if (r.sizes && typeof r.sizes === "object") h += `<div class="muted">sizes: ${esc(JSON.stringify(r.sizes))}</div>`;
  } else {
    h += `<div class="kv" data-testid="checks-count"><span>failing links: <b>${o.rows.length}</b></span></div>`;
  }
  rep.innerHTML = h;
  $("#tbl-toolout").style.display = o.rows.length ? "" : "none";
  if (o.rows.length) renderTable("toolout"); else $("#tbl-toolout").innerHTML = "";
}

/* ------------------------------------------------------------------ assistant */
function mdToHtml(src) {
  const inline = s => esc(s).replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>").replace(/`([^`]+)`/g, "<code>$1</code>");
  const lines = String(src || "").split("\n"); let out = "", i = 0;
  while (i < lines.length) {
    const l = lines[i];
    if (/^\s*\|.*\|\s*$/.test(l)) {
      const rows = []; while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) rows.push(lines[i++].trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
      const body = rows.filter(r => !r.every(c => /^:?-{2,}:?$/.test(c))), head = body.shift();
      out += `<table><thead><tr>${head.map(c => `<th>${inline(c)}</th>`).join("")}</tr></thead><tbody>${body.map(r => `<tr>${r.map(c => `<td>${inline(c)}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
    } else if (/^\s*[-*]\s+/.test(l)) {
      let li = ""; while (i < lines.length && /^\s*[-*]\s+/.test(lines[i])) li += `<li>${inline(lines[i++].replace(/^\s*[-*]\s+/, ""))}</li>`; out += `<ul>${li}</ul>`;
    } else if (l.trim()) { out += `<p>${inline(l)}</p>`; i++; } else i++;
  }
  return out;
}
function asstAdd(cls, html) { const log = $("#asst-log"), d = document.createElement("div"); d.className = "msg " + cls; d.innerHTML = html; log.appendChild(d); log.scrollTop = log.scrollHeight; return d; }
async function asstStatus() {
  try {
    const s = await jget("/assistant/status"), on = !!s.available;
    $("#asst-status").textContent = on ? `available (${s.model})` : `not available: ${s.reason}`;
    $("#asst-input").disabled = $("#asst-send").disabled = !on; state.asstOn = on;
  } catch (e) { $("#asst-status").textContent = "not available: " + e.message; $("#asst-input").disabled = $("#asst-send").disabled = true; state.asstOn = false; }
}
function asstSend() {
  const inp = $("#asst-input"), text = inp.value.trim();
  if (!text || !state.asstOn) return;
  if (!state.pid) { toast("Open a project first."); return; }
  inp.value = ""; asstAdd("user", `<p>${esc(text)}</p>`).dataset.testid = "asst-user";
  const wait = asstAdd("assistant", `<div class="muted">Thinking... (answers take 10-60 s)</div>`);
  inp.disabled = $("#asst-send").disabled = true; document.body.dataset.asstBusy = "1";
  const body = { project: state.pid, scenario: state.sid, message: text, history: state.history.slice(), model: $("#asst-model").value };
  enqueue(async () => {
    try {
      const r = await jpost("/assistant", body);
      state.history.push({ role: "user", content: text }, { role: "assistant", content: r.reply });
      const u = r.usage || {}, tc = (r.tool_calls || []);
      wait.dataset.testid = "asst-reply";
      wait.innerHTML = mdToHtml(r.reply) + tc.map(c => `<div class="tc ${c.ok === false ? "bad" : ""}" data-testid="asst-tool">tool: ${esc(c.name)}(${esc(JSON.stringify(c.input || {}).slice(0, 160))}) ${c.ok === false ? "failed" : "ok"}</div>`).join("") +
        `<div class="usage" data-testid="asst-usage">tokens: ${u.input_tokens ?? 0} in, ${u.output_tokens ?? 0} out, ${u.cache_write_tokens ?? 0} cache write, ${u.cache_read_tokens ?? 0} cache read</div>`;
      const info = await jget(`/projects/${state.pid}`);            // the assistant may have made new scenarios
      state.info.scenarios = info.scenarios; await loadResults(); renderAll();
    } catch (e) { wait.className = "msg err"; wait.textContent = e.message; }
    finally { document.body.dataset.asstBusy = "0"; if (state.asstOn) { inp.disabled = $("#asst-send").disabled = false; } $("#asst-log").scrollTop = $("#asst-log").scrollHeight; }
  });
}

/* ------------------------------------------------------------------ tabs */
function showTab(t) {
  state.tab = t;
  $$(".tab").forEach(b => b.classList.toggle("active", b.id === "tab-" + t));
  $$(".pane").forEach(p => p.classList.toggle("active", p.id === "pane-" + t));
  renderActiveTab();
}
function renderActiveTab() {
  const t = state.tab;
  if (t === "nodes" || t === "links" || t === "results") renderTable(t);
  else if (t === "settings") renderSettings();
  else if (t === "toolout") renderToolOut();
  else if (t === "hydro") drawHydro();
  else if (t === "profile") { if (!$("#prof-start").value) autoProfile(); else drawProfile(); }
}

/* ------------------------------------------------------------------ project actions */
async function openProject(info, fit = true) {
  state.pid = info.id; state.info = info; state.sid = "base"; state.sel = { table: null, ids: [] }; state.pipeStart = null;
  state.toolout = null; state.results = null; state.summary = null; state.storm = null; state.draw = null; state.catchPending = null;
  state.rain = { step_min: 5, duration_min: 60, mode: "idf", idf: [], series: [] }; state.rainSig = null; state.history = [];
  $("#asst-log").innerHTML = "";
  if (state.colorBy.startsWith("storm")) { state.colorBy = "v_ms"; $("#color-by").value = "v_ms"; }
  $("#prof-start").value = ""; $("#prof-end").value = ""; $("#settings-form").dataset.sig = "";
  await mapReady;
  map.setLayoutProperty("osm", "visibility", info.basemap && $("#basemap-toggle").checked ? "visible" : "none");
  await loadToolList();
  await refreshAll(true);
  if (!state.model.nodeFeat.length && !info.basemap) map.jumpTo({ center: [150 / M_LON, 100 / M_LAT], zoom: 17 });
  updateGrid(); setTool(state.tool);
}
async function withBusy(text, fn) { busy(true, text); try { await fn(); } catch (e) { toast(e.message || String(e)); } finally { busy(false); } }
function openNew() { $("#dlg-new").hidden = false; $("#new-name").focus(); }
async function openSampleDlg() {
  const list = $("#sample-list"); list.innerHTML = "Loading..."; $("#dlg-sample").hidden = false;
  try {
    const s = await jget("/samples");
    list.innerHTML = s.map(x => `<button data-case="${esc(x.id)}" id="sample-${esc(x.id)}">${esc(x.name)}</button>`).join(""); tag(list);
    $$("button", list).forEach(b => b.addEventListener("click", () => {
      $("#dlg-sample").hidden = true;
      enqueue(() => withBusy(`Building ${b.dataset.case} (19k pipes)...`, async () => openProject(await jpost(`/projects/sample/${b.dataset.case}`))));
    }));
  } catch (e) { list.textContent = e.message; }
}
function wireUi() {
  $("#new-btn").onclick = $("#welcome-new").onclick = openNew;
  $("#new-cancel").onclick = () => { $("#dlg-new").hidden = true; };
  $("#new-crs-mode").onchange = () => { $("#new-epsg-wrap").style.display = $("#new-crs-mode").value === "epsg" ? "" : "none"; };
  $("#new-create").onclick = () => {
    $("#dlg-new").hidden = true;
    const name = $("#new-name").value.trim() || "New project", crs = $("#new-crs-mode").value === "epsg" ? Number($("#new-epsg").value) || null : null;
    enqueue(() => withBusy("Creating project...", async () => openProject(await jpost("/projects/new", { name, crs }))));
  };
  $("#sample-btn").onclick = $("#welcome-sample").onclick = openSampleDlg;
  $("#sample-cancel").onclick = () => { $("#dlg-sample").hidden = true; };
  $("#open-btn").onclick = $("#welcome-open").onclick = () => $("#open-file").click();
  $("#open-file").onchange = e => {
    const f = e.target.files[0]; if (!f) return; e.target.value = "";
    enqueue(() => withBusy("Opening project...", async () => {
      const fd = new FormData(); fd.append("file", f);
      openProject(await (await api("/projects/open", { method: "POST", body: fd })).json());
    }));
  };
  $("#save-btn").onclick = () => enqueue(async () => {
    const r = await api(`/projects/${state.pid}/save?sid=${encodeURIComponent(state.sid)}`);
    const cd = r.headers.get("content-disposition") || "", mt = /filename="?([^";]+)"?/.exec(cd), blob = await r.blob();
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = mt ? mt[1] : "project.gpkg";
    document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
  });
  $("#scenario-select").onchange = e => enqueue(async () => { state.sid = e.target.value; state.sel = { table: null, ids: [] }; $("#settings-form").dataset.sig = ""; await refreshAll(false); });
  $("#copy-btn").onclick = () => enqueue(async () => {
    const r = await jpost(`${base()}/copy`, {}); state.info = r; state.sid = r.created; $("#settings-form").dataset.sig = ""; await refreshAll(false);
  });
  const hist = which => enqueue(async () => {
    const r = await jpost(`${base()}/${which}`); updateScenario(r.scenario); state.summary = r.summary;
    await loadModel(); await loadResults(); renderAll();
  });
  $("#undo-btn").onclick = () => hist("undo"); $("#redo-btn").onclick = () => hist("redo");
  $("#tools-btn").onclick = e => { e.stopPropagation(); $("#tools-menu").hidden = !$("#tools-menu").hidden; };
  document.addEventListener("click", () => { $("#tools-menu").hidden = true; });
  $("#color-by").onchange = e => { state.colorBy = e.target.value; mergeResults(); renderLegend(); pushMap(); };
  $("#basemap-toggle").onchange = e => { if (state.info && state.info.basemap) map.setLayoutProperty("osm", "visibility", e.target.checked ? "visible" : "none"); };
  $$(".tool").forEach(b => b.addEventListener("click", () => setTool(b.id.slice(5))));
  $$(".tab").forEach(b => b.addEventListener("click", () => showTab(b.id.slice(4))));
  $("#hydro-attr").onchange = drawHydro;
  $("#asst-form").addEventListener("submit", e => { e.preventDefault(); asstSend(); });
  $("#asst-input").addEventListener("keydown", e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); asstSend(); } });
  $("#import-btn").onclick = () => $("#import-file").click();
  $("#import-file").onchange = e => {
    const f = e.target.files[0]; if (!f) return; e.target.value = "";
    enqueue(() => withBusy("Importing SWMM model...", async () => {
      const fd = new FormData(); fd.append("file", f);
      await openProject(await (await api("/projects/import", { method: "POST", body: fd })).json());
    }));
  };
  $("#export-btn").onclick = () => enqueue(async () => saveBlob(await api(`/projects/${state.pid}/export.inp?sid=${encodeURIComponent(state.sid)}`), "model.inp"));
  $("#prof-draw").onclick = drawProfile;
  $("#prof-start").addEventListener("keydown", e => { if (e.key === "Enter") drawProfile(); });
  $("#prof-end").addEventListener("keydown", e => { if (e.key === "Enter") drawProfile(); });
  document.addEventListener("keydown", e => {
    const tg = e.target.tagName; if (["INPUT", "SELECT", "TEXTAREA"].includes(tg)) return;
    const k = e.key.toLowerCase();
    if (e.ctrlKey && k === "z") { e.preventDefault(); $("#undo-btn").click(); }
    else if (e.ctrlKey && k === "y") { e.preventDefault(); $("#redo-btn").click(); }
    else if (k === "enter" && state.tool === "catchment") finishCatchment();
    else if (k === "escape") { state.pipeStart = null; state.movePick = null; if (state.tool === "catchment") setTool("catchment"); setSel(null, []); }
    else if (k === "delete" && state.sel.ids.length) { const t = state.sel.table, ids = state.sel.ids.slice(); enqueue(() => deleteIds(t, ids)); }
    else if (!e.ctrlKey) { const m = { s: "select", m: "manhole", o: "outfall", w: "wetwell", p: "pipe", v: "move", c: "catchment" }[k]; if (m) setTool(m); }
  });
}

/* ------------------------------------------------------------------ boot */
state.history = [];
initMap(); wireUi(); initTables(); tag(); renderLegend(); updateStatus(); updateButtons(); asstStatus();
window.ed = {
  state, map,
  clickAt: (lon, lat, mods) => enqueue(() => act({ lng: lon, lat: lat }, mods)),
  selectElement: (table, id) => { setSel(table, [String(id)], { zoom: false }); return chain; },
  counts: () => state.model ? { nodes: state.model.nodeFeat.length, links: state.model.linkFeat.length } : { nodes: 0, links: 0 },
  idle: () => chain,
  finish: () => { finishCatchment(); return chain; },
};
