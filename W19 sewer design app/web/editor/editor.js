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
  draw: null, catchPending: null, storm: null, source: "engine", stored: null, storedCache: {},
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
function toast(msg, kind = "err") {
  const t = $("#toast"); t.textContent = msg; t.hidden = false; t.classList.toggle("err", kind === "err");
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
const NO_FAIL = new Set(["compare", "storm_q", "storm_cap", "storm_flood"]);     // colourings the steady checks' red overlay would mislead
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
  if (by === "compare") {
    const c = state.compare && state.compare.b === state.sid ? state.compare : null;
    if (!c) { el.innerHTML = `<div class="t">Change</div><div class="r muted">Scenarios... &gt; Compare first</div>`; return; }
    const lab = { size: "size changed", levels: "levels changed", flow: "flow changed only", added: "new pipe", same: "unchanged" };
    el.innerHTML = `<div class="t">Against ${esc(c.aName)}</div>` + Object.entries(CHANGE_COL).map(([k, col]) => `<div class="r"><span class="sw" style="background:${col}"></span>${lab[k]} (${c.counts[k] ?? 0})</div>`).join("") +
      (c.counts.removed ? `<div class="r muted">${c.counts.removed} pipes only in ${esc(c.aName)}</div>` : "");
    return;
  }
  if (by.startsWith("storm") && !stormNow()) { el.innerHTML = `<div class="t">${SCALES[by].title}</div><div class="r muted">run Tools &gt; Run on EPA SWMM first</div>`; return; }
  const rows = by === "none" || by === "storm_flood" ? [] : SCALES[by].bins.map(b => [b[2], b[1]]);
  el.innerHTML = (by === "none" ? "" : `<div class="t">${SCALES[by].title}${stale ? " (before the last edit)" : ""}</div>`) +
    rows.map(r => `<div class="r"><span class="sw" style="background:${r[0]}"></span>${esc(r[1])}</div>`).join("") +
    (by === "storm_flood" ? `<div class="r"><span class="sw" style="background:#d7301f;height:9px;border-radius:5px;width:9px"></span>node flooding</div>` : "") +
    (NO_FAIL.has(by) ? "" : `<div class="r fail-row" data-testid="legend-fail" title="Click to ${ui.showFail ? "hide" : "show"} the failing pipes"><span class="sw" style="background:#d7301f;${ui.showFail ? "" : "opacity:.3"}"></span>failing ${ui.showFail ? "(drawn on top)" : "(hidden)"}</div>`) +
    `<div class="r"><span class="sw" style="background:repeating-linear-gradient(90deg,#7b3fa0 0 5px,transparent 5px 8px)"></span>pump</div>`;
}

/* ------------------------------------------------------------------ map */
/* basemaps: keyless raster tiles for on-screen display only (never captured into client reports) */
const ESRI = "https://server.arcgisonline.com/ArcGIS/rest/services/";
const abc = u => ["a", "b", "c"].map(s => u.replace("{s}", s));
const BASEMAPS = {
  osm: { tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], maxzoom: 19, attribution: "&copy; OpenStreetMap contributors" },
  sat: { tiles: [ESRI + "World_Imagery/MapServer/tile/{z}/{y}/{x}"], maxzoom: 18, attribution: "Imagery &copy; Esri, Maxar, Earthstar Geographics" },
  topo: { tiles: abc("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png"), maxzoom: 17, attribution: "&copy; OpenStreetMap contributors, SRTM | &copy; OpenTopoMap (CC-BY-SA)" },
  // Carto's keyless tiles now carry an "API key required" watermark: Esri's grey canvas maps instead
  light: { tiles: [ESRI + "Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"], maxzoom: 16, attribution: "&copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors" },
  dark: { tiles: [ESRI + "Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"], maxzoom: 16, attribution: "&copy; Esri, HERE, Garmin, &copy; OpenStreetMap contributors" },
};
function initMap() {
  const sources = {}, layers = [{ id: "bg", type: "background", paint: { "background-color": "#f3f5f8" } }];
  for (const [k, b] of Object.entries(BASEMAPS)) {
    sources["bm-" + k] = { type: "raster", tiles: b.tiles, tileSize: 256, maxzoom: b.maxzoom, attribution: b.attribution };
    layers.push({ id: "bm-" + k, type: "raster", source: "bm-" + k, layout: { visibility: "none" } });
  }
  sources.dem = { type: "raster-dem", tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"], encoding: "terrarium", tileSize: 256, maxzoom: 15, attribution: "Terrain: Mapzen, AWS Open Data" };
  layers.push({ id: "hillshade", type: "hillshade", source: "dem", layout: { visibility: "none" }, paint: { "hillshade-exaggeration": 0.35, "hillshade-shadow-color": "#3d4a5c", "hillshade-highlight-color": "#ffffff" } });
  for (const [k, svc] of [["sat-roads", "Reference/World_Transportation"], ["sat-labels", "Reference/World_Boundaries_and_Places"]]) {
    sources[k] = { type: "raster", tiles: [ESRI + svc + "/MapServer/tile/{z}/{y}/{x}"], tileSize: 256, maxzoom: 18, attribution: "&copy; Esri" };
    layers.push({ id: k, type: "raster", source: k, layout: { visibility: "none" } });
  }
  map = new maplibregl.Map({
    container: "map", center: [0.001, 0.0005], zoom: 17, boxZoom: false, doubleClickZoom: false, attributionControl: { compact: true },
    style: { version: 8, glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf", sources, layers },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
  mapReady = new Promise(res => {
    let done = false; const go = () => { if (!done) { done = true; res(); } };
    map.on("load", go);
    const t = setInterval(() => { if (map.style && map.style._loaded) { clearInterval(t); go(); } }, 50);
  }).then(() => {
    const E = { type: "FeatureCollection", features: [] };
    for (const id of ["grid", "catch", "catch-links", "drawpoly", "links", "nodes", "sel-links", "sel-nodes", "drag", "hot", "measure", "route", "cursor"]) map.addSource(id, { type: "geojson", data: E, tolerance: 0.4 });
    map.addLayer({ id: "grid", type: "line", source: "grid", paint: { "line-color": "#d6dde6", "line-width": 1 } });
    map.addLayer({ id: "catch", type: "fill", source: "catch", paint: { "fill-color": "#4aa3a2", "fill-opacity": 0.22 } });
    map.addLayer({ id: "catch-line", type: "line", source: "catch", paint: { "line-color": "#2d7f7e", "line-width": 1.5 } });
    map.addLayer({ id: "catch-links", type: "line", source: "catch-links", paint: { "line-color": "#2d7f7e", "line-width": 1.2, "line-dasharray": [1, 2] } });
    map.addLayer({ id: "drawpoly-fill", type: "fill", source: "drawpoly", filter: ["==", ["geometry-type"], "Polygon"], paint: { "fill-color": "#e6821e", "fill-opacity": 0.2 } });
    map.addLayer({ id: "drawpoly-line", type: "line", source: "drawpoly", paint: { "line-color": "#e6821e", "line-width": 2, "line-dasharray": [2, 1] } });
    map.addLayer({ id: "drawpoly-pts", type: "circle", source: "drawpoly", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 4, "circle-color": "#e6821e" } });
    // pipe width grows with size and zoom (zoom must be the outer interpolation); big pipes draw on top
    const dn = ["case", ["has", "section"], 900, ["coalesce", ["get", "dn_mm"], 200]];   // a box or channel section draws as a large conduit
    const w = (k, add = 0) => ["interpolate", ["linear"], ["zoom"],
      10, ["+", add, ["*", k, ["step", dn, 0.7, 300, 1.2, 600, 2, 1000, 2.8]]],
      15, ["+", add, ["*", k, ["step", dn, 2, 300, 3, 600, 4.4, 1000, 6]]],
      19, ["+", add, ["*", k, ["step", dn, 4, 300, 6, 600, 9, 1000, 12]]]];
    map.addLayer({ id: "links-casing", type: "line", source: "links", layout: { "line-cap": "round", "line-sort-key": dn }, paint: { "line-color": "#ffffff", "line-opacity": 0.75, "line-width": w(1, 2) } });
    map.addLayer({ id: "links-base", type: "line", source: "links", layout: { "line-cap": "round", "line-sort-key": dn }, paint: { "line-color": ["get", "_c"], "line-width": w(1) } });
    map.addLayer({ id: "links-fail", type: "line", source: "links", filter: ["==", ["get", "_fail"], 1], layout: { "line-cap": "round" }, paint: { "line-color": "#d7301f", "line-width": w(1.3, 0.5) } });
    map.addLayer({ id: "links-pump", type: "line", source: "links", filter: ["==", ["get", "kind"], "pump"], paint: { "line-color": "#7b3fa0", "line-width": w(1.3), "line-dasharray": [2, 1.5] } });
    map.addLayer({ id: "links-locked", type: "line", source: "links", filter: ["==", ["get", "_lock"], 1], paint: { "line-color": "#ffffff", "line-width": w(0.35), "line-dasharray": [1.5, 1.5] } });
    map.addImage("flow-arrow", arrowImage(), { sdf: true, pixelRatio: 2 });
    map.addLayer({ id: "links-arrow", type: "symbol", source: "links", minzoom: 15.5, layout: { "symbol-placement": "line", "symbol-spacing": 90, "icon-image": "flow-arrow", "icon-size": 1.25, "icon-rotation-alignment": "map", "icon-allow-overlap": true, "icon-ignore-placement": true }, paint: { "icon-color": "#1d2733", "icon-opacity": 0.75 } });
    map.addLayer({ id: "links-label", type: "symbol", source: "links", minzoom: 17, layout: { "symbol-placement": "line", "text-field": ["get", "_lab"], "text-size": 10.5, "text-font": ["Open Sans Semibold"], "text-offset": [0, -0.9], "symbol-spacing": 260 }, paint: { "text-color": "#1d2733", "text-halo-color": "#fff", "text-halo-width": 1.6 } });
    map.addLayer({ id: "hot-link", type: "line", source: "hot", paint: { "line-color": "#ffb000", "line-width": w(1, 5), "line-opacity": 0.85 } });
    map.addLayer({ id: "sel-links-casing", type: "line", source: "sel-links", paint: { "line-color": "#fff", "line-width": 9 } });
    map.addLayer({ id: "sel-links", type: "line", source: "sel-links", paint: { "line-color": "#00b3c7", "line-width": 5 } });
    const kc = ["match", ["get", "kind"], "outfall", "#123e7c", "wetwell", "#7b3fa0", "storage", "#1b9e77", "junction", "#c9a227", "#8a94a0"];
    const fl = ["==", ["coalesce", ["get", "_fl"], 0], 1];
    // at city scale plain manholes are hidden (they read as grey dots over the pipes); outfalls, wet wells and flagged nodes stay
    const mh = ["all", ["==", ["get", "kind"], "manhole"], ["!", fl]];
    map.addLayer({ id: "nodes", type: "circle", source: "nodes", paint: {
      "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, ["case", fl, 3.5, mh, 0, 3.5], 13.5, ["case", fl, 5, mh, 0, 4.5], 14.5, ["case", fl, 6, mh, 2.6, 5], 16, ["case", fl, 8, mh, 4.5, 6.5], 19, ["case", fl, 12, mh, 8, 10]],
      "circle-color": ["case", fl, "#d7301f", kc], "circle-stroke-color": "#fff",
      "circle-stroke-width": ["interpolate", ["linear"], ["zoom"], 13.5, ["case", mh, 0, 1.4], 14.5, 1.2] } });
    map.addLayer({ id: "nodes-label", type: "symbol", source: "nodes", minzoom: 15.5, layout: { "text-field": ["get", "id"], "text-size": 11, "text-offset": [0, 1.1], "text-anchor": "top", "text-font": ["Open Sans Semibold"], "text-allow-overlap": false }, paint: { "text-color": "#1d2733", "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    map.addLayer({ id: "sel-nodes", type: "circle", source: "sel-nodes", paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 5, 19, 12], "circle-color": "rgba(0,0,0,0)", "circle-stroke-color": ["case", ["==", ["get", "_pend"], 1], "#e6821e", "#00b3c7"], "circle-stroke-width": 3 } });
    map.addLayer({ id: "drag", type: "circle", source: "drag", paint: { "circle-radius": 8, "circle-color": "rgba(230,130,30,.35)", "circle-stroke-color": "#e6821e", "circle-stroke-width": 2 } });
    map.addLayer({ id: "route-halo", type: "line", source: "route", filter: ["==", ["geometry-type"], "LineString"], layout: { "line-cap": "round", "line-join": "round" },
      paint: { "line-color": "#ff7a1a", "line-opacity": 0.6, "line-blur": 1, "line-width": ["interpolate", ["linear"], ["zoom"], 10, 8, 15, 15, 19, 26] } }, "links-casing");
    map.addLayer({ id: "route-pts", type: "circle", source: "route", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 9, "circle-color": "#ff7a1a", "circle-stroke-color": "#fff", "circle-stroke-width": 2 } });
    map.addLayer({ id: "route-lab", type: "symbol", source: "route", filter: ["==", ["geometry-type"], "Point"], layout: { "text-field": ["get", "lab"], "text-size": 11, "text-font": ["Open Sans Semibold"], "text-allow-overlap": true }, paint: { "text-color": "#fff" } });
    map.addLayer({ id: "cursor", type: "circle", source: "cursor", paint: { "circle-radius": 7, "circle-color": "#ff7a1a", "circle-stroke-color": "#fff", "circle-stroke-width": 2.5 } });
    map.addLayer({ id: "measure-line", type: "line", source: "measure", paint: { "line-color": "#e6821e", "line-width": 2.5, "line-dasharray": [2, 1] } });
    map.addLayer({ id: "measure-pts", type: "circle", source: "measure", filter: ["==", ["geometry-type"], "Point"], paint: { "circle-radius": 4, "circle-color": "#fff", "circle-stroke-color": "#e6821e", "circle-stroke-width": 2 } });
    map.on("moveend", updateGrid);
    updateGrid(); applyBasemap(); applyTheme();
  });
  map.on("click", e => { if (suppressClick) return; if (state.tool === "move") return; enqueue(() => act(e.lngLat, e.originalEvent)); });
  map.on("dblclick", e => { e.preventDefault(); if (state.tool === "catchment") finishCatchment(); });
  map.on("mousemove", e => { map.getCanvas().style.cursor = state.pid ? (state.tool === "select" ? "" : "crosshair") : ""; if (dragging) dragMove(e.lngLat); hover(e); });
  map.on("mouseout", () => { $("#maptip").hidden = true; setHot(null); });
  map.on("zoomend", () => showCoords());
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
  const cat = (d.settings && d.settings.design && d.settings.design.catalogue) || [];          // the scenario's own sizes
  if (state.info && cat.length) state.info.catalogue = cat.map(r => r[0]).sort((a, b) => a - b);
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
  const key = state.pid + "/" + state.sid;
  if (!(key in state.storedCache)) { const st = await jget(`${base()}/stored`); state.storedCache[key] = Object.values(st.links || {}).some(r => r && r.q_ls != null) ? st.links : null; }   // a model that holds no results offers none
  state.stored = state.storedCache[key];
  if (!state.stored && state.source === "stored") { state.source = "engine"; $("#results-source").value = "engine"; }
  $("#results-source").querySelector("option[value=stored]").disabled = !state.stored;
  state.results = r; state.summary = r.summary; mergeResults(); renderToolsMenu();
}
const usingStored = () => state.source === "stored" && !!state.stored;
const srcLinks = () => usingStored() ? state.stored : (state.results ? state.results.links : {});
function mergeResults() {
  const m = state.model, R = srcLinks(); if (!m) return;
  const by = state.colorBy, S = by.startsWith("storm") ? stormNow() : null;
  if (by === "storm_q" && S) {
    const mx = Math.max(1e-9, ...Object.values(S.links).map(x => x.q_peak || 0)), cs = ["#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#6a51a3", "#4a1486"];
    SCALES.storm_q.bins = [0.05, 0.15, 0.35, 0.6, 0.85, 1e9].map((k, i) => [k * mx, i === 5 ? `over ${+(0.85 * mx).toPrecision(3)}` : `up to ${+(k * mx).toPrecision(3)}`, cs[i]]);
  }
  const E = state.results ? state.results.links : {}, LK = lockedSet(), CM = state.compare && state.compare.b === state.sid ? state.compare.change : null;
  const FR = state.stormFrame && state.stormFrame.sid === state.sid ? state.stormFrame : null;
  for (const f of m.linkFeat) {
    const r = R[f.id], p = f.properties, sl = S && S.links[f.id], e = E[f.id];
    p._lab = p.kind === "pump" ? `pump ${f.id}` : p.section ? `section ${p.section}` : `DN${p.dn_mm ?? "?"}` + (e && e.s_pc != null ? ` · ${(+e.s_pc).toFixed(2)} %` : "");
    p._fail = !usingStored() && !NO_FAIL.has(by) && r && (r.over_limit || r.over_vmax || r.surcharged || r.negative_slope) ? 1 : 0;
    p._lock = LK.has(String(f.id)) ? 1 : 0;
    const sq = FR ? (FR.links[f.id] == null ? null : Math.abs(FR.links[f.id])) : sl && sl.q_peak, scap = FR ? FR.links[f.id] : sl && sl.capacity_peak;
    p._c = by === "compare" ? CHANGE_COL[(CM && CM[f.id]) || "same"] : by === "dn_mm" && usingStored() ? colourFor(by, p.dn_mm) : by === "storm_q" ? colourFor(by, sq) : by === "storm_cap" ? colourFor(by, scap) : by === "storm_flood" ? GREY : colourFor(by, r && r[by]);
    if (p.section && p._c === GREY && by !== "none") p._c = "#4b5563";                  // not analysed: dark enough to see on any basemap
  }
  const wasFl = m.hasFl; let anyFl = false;
  for (const f of m.nodeFeat) {
    const fl = by === "storm_flood" && S && (FR ? (FR.flooding[f.id] || 0) > 0 : S.nodes[f.id] && S.nodes[f.id].flooding_peak > 0) ? 1 : 0;
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
  const reread = r.structural || op.op === "set_many" || op.op === "set_loads" || op.op === "lock" || op.op === "set_section" || (op.op === "set" && op.table === "nodes" && op.field === "invert");
  if (reread) await loadModel(); else patchLocal(op);
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
  // a non-zero count is a link: each click steps to the next pipe with that flag
  const cnt = k => s[k] ? `<a class="fail" data-flag="${k}" title="Click to step through them on the map">${s[k]}</a>` : `<b>0</b>`;
  el.innerHTML = `solved ${s.links} links in ${num(s.seconds, 3)} s &middot; ${num(s.km, 2)} km &middot; over d/D limit ${cnt("over_limit")}` +
    ` &middot; over v max ${cnt("over_vmax")} &middot; surcharged ${cnt("surcharged")}` +
    (s.not_analysed ? ` &middot; <span class="warn" title="Box or open-channel sections: drawn and editable, not analysed by the steady engine">${s.not_analysed} non-circular sections not analysed</span>` : "") +
    (s.km_under_vmin == null ? ` &middot; <span class="muted" title="Choose a check load set in Settings, Flows">self-cleansing not checked</span>`
                             : ` &middot; ${num(s.km_under_vmin, 2)} km under v min at ${esc(s.check_set)}`) + (s.negative_slope ? ` &middot; ${cnt("negative_slope")} <span class="bad">flat or adverse</span>` : "") +
    (bad === 0 && s.links && !s.not_analysed ? ` <span class="ok">&#10003;</span>` : "");
}
function updateButtons() {
  const has = !!state.pid, sc = scenario();
  for (const id of ["save-btn", "copy-btn", "tools-btn", "export-btn", "export-dxf-btn", "export-csv-btn"]) $("#" + id).disabled = !has;
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
  $("#results-src").textContent = usingStored() ? "SewerGEMS (stored results)" : "W19 engine";
  updateStatus(); updateButtons(); pushMap(); renderProps(); renderActiveTab(); renderLegend(); stormBar();
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
  measure: "Click points along the route to measure; Esc clears.",
};
function setTool(t) {
  if (t !== "measure") clearMeasure();
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
  if (state.routePick) { const id = nn ? nn.id : nl ? nl.id : null; if (id) pickStop(id); else toast("Click a manhole or a pipe.", "info"); return; }
  if (t === "measure") { addMeasure(ll); return; }
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
  if (state.tab === "profile" && !opt.keepProfile) autoProfile();
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
  let h = traceBox() + `<h4 data-testid="prop-title">${head}</h4>`;
  if (table === "links") {
    const LK = lockedSet(), n = state.sel.ids.filter(i => LK.has(i)).length;
    h += `<div class="trace-bar">Design <button id="lock-on" title="The design keeps these pipes' size and levels">Lock</button><button id="lock-off">Unlock</button>` +
      `<span class="muted" data-testid="lock-state">${n ? (n === state.sel.ids.length ? "locked" : `${n} of ${state.sel.ids.length} locked`) : "free"}</span></div>`;
  }
  if (!multi && (table === "nodes" || table === "links")) h += `<div class="trace-bar">Trace <button id="trace-up" title="Everything that drains here (U)">&#8593; Upstream</button><button id="trace-down" title="The way to the outfall (D)">&#8595; Downstream</button></div>`;
  if (table === "links" && fs.every(f => f.properties.kind === "conduit")) h += sectionEditor(fs);
  for (const k of keys) {
    if (k === "sec" || k === "section") continue;                                   // shown by the section editor
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
      const cur = val(field); if (cur !== undefined && (cur === v || (typeof cur === "number" && +cur.toFixed(4) === v))) return;   // unchanged as shown
      if (inp._sent === v) return; inp._sent = v;
      const ids = state.sel.ids.slice(), tb = state.sel.table;
      enqueue(() => setField(tb, ids, field, v));
    };
    inp.addEventListener("focus", () => { inp._sent = undefined; });
    inp.addEventListener("change", go);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { go(); inp.blur && inp.blur(); } });
  });
  wireSectionEditor();
  $$("[data-kind=load]", host).forEach(inp => {
    const go = () => { if (inp.value === "" || inp._sent === inp.value) return; inp._sent = inp.value; const v = Number(inp.value), set = inp.dataset.set, ids = state.sel.ids.slice(); enqueue(() => execMany(ids.map((n, k) => ({ op: "set_load", set, node: n, value: v })))); };
    inp.addEventListener("focus", () => { inp._sent = undefined; });
    inp.addEventListener("change", go);
    inp.addEventListener("keydown", e => { if (e.key === "Enter") { go(); inp.blur(); } });
  });
  renderResultsBlock();
}
const szLab = r => r.section ? String(r.section) : "DN" + r.dn_mm;
/* ---- cross-section: a catalogue circle, or a box, open rectangle or trapezoid with its own n (op set_section) */
const SEC_SHAPES = [["circle", "Circular (catalogue size)"], ["box", "Box (closed rectangle)"], ["rect_open", "Open rectangle"], ["trapezoid", "Trapezoid (open)"]];
const SEC_FIELDS = { box: [["span_m", "Span (width)", "m"], ["rise_m", "Rise (height)", "m"], ["n", "Manning's n", ""], ["barrels", "Barrels", ""]],
  rect_open: [["span_m", "Width", "m"], ["rise_m", "Bank height", "m"], ["n", "Manning's n", ""], ["barrels", "Barrels", ""]],
  trapezoid: [["bottom_m", "Bottom width", "m"], ["z_left", "Side slope left (H:1V)", ""], ["z_right", "Side slope right (H:1V)", ""], ["rise_m", "Bank height", "m"], ["n", "Manning's n", ""], ["barrels", "Barrels", ""]] };
function sectionEditor(fs) {
  const s0 = fs[0].properties.sec, same = fs.every(f => JSON.stringify(f.properties.sec || null) === JSON.stringify(s0 || null));
  const shape = !same ? "" : s0 ? s0.shape : "circle";
  let h = `<h5>Cross-section</h5><div class="pr"><label for="sec-shape">Shape</label><select id="sec-shape" data-testid="sec-shape">` +
    (shape === "" ? `<option value="" selected>mixed</option>` : "") + SEC_SHAPES.map(([v, l]) => `<option value="${v}"${v === shape ? " selected" : ""}>${l}</option>`).join("") + `</select><span></span></div>`;
  h += `<div id="sec-fields">${secFieldsHtml(shape, same ? s0 : null)}</div>`;
  h += `<div class="row"><button id="sec-apply" data-testid="sec-apply" title="Apply the section to the ${fs.length > 1 ? fs.length + " selected conduits" : "conduit"} (one undoable edit)">Apply section</button></div>`;
  return h;
}
function secFieldsHtml(shape, s) {
  if (shape === "circle") return `<p class="muted">Sized from the pipe catalogue (dn_mm below); the d/D limits and velocities of the sewer rules apply.</p>`;
  const F = SEC_FIELDS[shape]; if (!F) return "";
  const dflt = { span_m: 2, rise_m: 1.5, bottom_m: 2, z_left: 1.5, z_right: 1.5, n: shape === "box" ? 0.015 : 0.02, barrels: 1 };
  return F.map(([k, l, u]) => `<div class="pr"><label for="sec-${k}">${l}</label><input type="number" step="any" min="0" id="sec-${k}" data-testid="sec-${k}" value="${s && s[k] != null ? +(+s[k]).toFixed(4) : dflt[k]}"><span class="u">${u}</span></div>`).join("") +
    `<p class="muted">Solved by Manning's equation at normal depth with this n; the sewer d/D limit and v max do not apply.${shape === "box" ? " A box that cannot carry its flow with a free surface is surcharged." : " Over the bank height it is overtopped (shown as surcharged)."}</p>`;
}
function wireSectionEditor() {
  const sel = $("#sec-shape"); if (!sel) return;
  sel.onchange = () => { $("#sec-fields").innerHTML = secFieldsHtml(sel.value, null); };
  $("#sec-apply").onclick = () => {
    const shape = sel.value, ids = state.sel.ids.slice(); if (!shape) return;
    if (shape === "circle") {
      const d = $("#prop-dn_mm"), dn = d && state.info && state.info.catalogue.includes(+d.value) ? +d.value : undefined;
      enqueue(() => exec(dn ? { op: "set_section", ids, section: null, dn_mm: dn } : { op: "set_section", ids, section: null })); return;
    }
    const s = { shape }; let bad = null;
    for (const [k, l] of SEC_FIELDS[shape]) { const v = Number($("#sec-" + k).value); if (!isFinite(v) || v < 0 || ((k === "rise_m" || k === "n" || k === "span_m") && !(v > 0)) || (k === "barrels" && !(Number.isInteger(v) && v >= 1))) bad = l; s[k] = v; }
    if (bad) { toast(`${bad}: give a positive number.`); return; }
    enqueue(() => exec({ op: "set_section", ids, section: s }));
  };
}
function control(table, k, ty, v) {
  const a = `id="prop-${k}" data-testid="prop-${k}" data-field="${k}" data-type="${ty}"`, vs = v === undefined ? "" : esc(typeof v === "number" ? +v.toFixed(4) : (v ?? ""));   // shown to 0.1 mm; sent only if edited
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
  const R = srcLinks(), sg = usingStored();
  if (state.sel.table !== "links" || state.sel.ids.length !== 1) { host.innerHTML = ""; return; }
  const r = R[state.sel.ids[0]];
  if (!r) { host.innerHTML = `<h5>Results</h5><p class="muted">No result (the network could not be solved, or this is a pump).</p>`; return; }
  const rows = sg ? [["q_ls", "Flow (L/s)"], ["v_ms", "Velocity (m/s)"], ["depth_m", "Depth (m)"], ["d_over_D", "d/D"]] : [["q_ls", "Flow (L/s)"], ["v_ms", "Velocity (m/s)"], ["d_over_D", "d/D"], ["limit", "d/D limit"], ["s_pc", "Slope (%)"]];
  if (r.depth_m != null && !sg) rows.splice(2, 2, ["depth_m", "Normal depth (m)"], ["d_over_D", "Depth / rise"], ["yc_m", "Critical depth (m)"], ["q_full_ls", "Full capacity (L/s)"]);
  if (sg && r.yn_sg_m != null) rows.push(["yn_sg_m", "Normal depth (m)"], ["yc_sg_m", "Critical depth (m)"]);
  let h = `<h5>Results ${sg ? "from SewerGEMS (stored)" : "(W19 engine)"}, read-only</h5>`;
  for (const [k, l] of rows) h += `<div class="pr"><label>${l}</label><span data-testid="res-${k}">${num(r[k], 4)}</span><span></span></div>`;
  const fl = sg ? [] : ["over_limit", "over_vmax", "surcharged", "negative_slope", "under_vmin"].filter(k => r[k]);
  if (!sg) h += `<div class="pr"><label>Flags</label><span class="${fl.length ? "flag" : ""}" data-testid="res-flags">${fl.length ? fl.join(", ") : "none"}</span><span></span></div>`;
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
const FLAGS = { over_limit: "d/D limit", over_vmax: "v max", surcharged: "surcharged", negative_slope: "flat or adverse", under_vmin: "v min" };
function flagText(r) { return Object.keys(FLAGS).filter(k => r && r[k]).map(k => FLAGS[k]).join(", "); }
function rowsFor(kind) {
  const m = state.model; if (!m) return [];
  const R = srcLinks(), sg = usingStored();
  if (kind === "nodes") { const ls = m.loads[m.settings.design_load] || {}; return m.nodeFeat.map(f => ({ ...f.properties, load: ls[f.id] ?? 0 })); }
  if (kind === "links") return m.linkFeat.map(f => f.properties);
  if (kind === "results") return m.linkFeat.filter(f => R[f.id]).map(f => sg ? ({ id: String(f.id), dn_mm: f.properties.dn_mm, ...R[f.id] }) : ({ id: String(f.id), ...R[f.id], flags: flagText(R[f.id]) }));
  if (kind === "toolout") return (state.toolout && state.toolout.rows || []).map(r => ({ ...r, flags: flagText(r) }));
  return [];
}
function colsOf(kind) { if (kind === "results" && usingStored()) return ["id", "dn_mm", "q_ls", "v_ms", "depth_m", "d_over_D"]; return kind === "toolout" && state.toolout && state.toolout.cols ? state.toolout.cols : { nodes: NODE_COLS, links: LINK_COLS, results: RES_COLS, toolout: TOOL_COLS }[kind]; }
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
  tbl.innerHTML = `<thead><tr>${cols.map(c => `<th data-col="${c}" class="${c === k ? "sorted" + (d < 0 ? " desc" : "") : ""}">${kind === "toolout" ? esc(REPORT_LABEL[c] || c) : c}</th>`).join("")}</tr></thead><tbody>` +
    slice.map(r => `<tr data-id="${esc(r.id)}" class="${sel.has(String(r.id)) ? "sel" : ""}">${cols.map(c => {
      const v = r[c], cur = state.cell && state.cell.kind === kind && state.cell.col === c && state.cell.id === String(r.id);
      return `<td class="${c === "flags" ? "flag" : ""}${cur ? " cur" : ""}">${esc(typeof v === "number" ? +v.toFixed(4) : v)}</td>`;
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
/* ---- profile: a long section along a route. From a start (manhole or pipe) down to the outfall, or to an end
   through any via points along the network in either direction. The route is lit on the map; the cursor on the map
   and on the profile follow each other. The profile zooms (wheel) and pans (drag) along the chainage. */
let profSeq = 0;
const prof = { rows: null, segs: [], range: null, view: null, cursor: null, drag: null };
function autoProfile() {
  const m = state.model; if (!m || state.routePick) return;
  if ($("#prof-end").value.trim() || $("#prof-via").value.trim()) { drawProfile(true); return; }   // a set route stays until changed
  let start = "";
  if (state.sel.table === "nodes" && state.sel.ids.length) start = state.sel.ids[0];
  else if (state.sel.table === "links" && state.sel.ids.length) start = state.sel.ids[0];          // a pipe: the section starts with it
  if (start) $("#prof-start").value = start;
  drawProfile();
}
async function drawProfile(keepRange) {
  const start = $("#prof-start").value.trim(), end = $("#prof-end").value.trim(), via = $("#prof-via").value.trim();
  const msg = $("#prof-msg"), svg = $("#profile-svg");
  if (!state.pid) return;
  if (!start) { msg.textContent = "Select a manhole or pipe, type a start, or use Pick on map."; svg.innerHTML = ""; setRoute(null); return; }
  const seq = ++profSeq;
  try {
    const q = new URLSearchParams({ start }); if (end) q.set("end", end); if (via) q.set("via", via);
    const rows = await jget(`${base()}/profile?${q}`);
    if (seq !== profSeq) return;
    if (keepRange !== true) { prof.range = null; prof.vz = 1; prof.vmid = null; }
    const len = rows.length ? rows[rows.length - 1].ch1 : 0, rev = rows.filter(r => r.reversed).length;
    msg.textContent = rows.length ? `${rows.length} links, ${num(len, 1)} m, ${rows[0].from_node} to ${rows[rows.length - 1].to_node}` +
      (end ? "" : " (the outfall)") + (rev ? `, ${rev} against the flow` : "") : "No links.";
    setRoute(rows); renderProfile(rows);
  } catch (e) { if (seq !== profSeq) return; msg.textContent = e.message; svg.innerHTML = ""; setRoute(null); }
}
function niceStep(span, n) { const raw = span / n, p = Math.pow(10, Math.floor(Math.log10(raw))); return ([1, 2, 5, 10].map(k => k * p).find(v => v >= raw)) || p * 10; }
const lerp = (a, b, f) => a == null || b == null ? null : a + (b - a) * f;
function renderProfile(rows) {
  state.lastProfile = rows; prof.rows = rows;
  const svg = $("#profile-svg"), wrap = $("#prof-wrap");
  const W = Math.max(520, wrap.clientWidth - 16), H = Math.max(190, wrap.clientHeight - 6);
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`);
  if (!rows.length) { svg.innerHTML = `<text x="20" y="30">No links.</text>`; prof.view = null; return; }
  const bands = ui.profBands, NB = bands ? 4 : 0;
  const L = 64, R = 18, T = 26, B = 20 + NB * 14 + 24, pw = W - L - R, ph = Math.max(60, H - T - B);
  const total = rows[rows.length - 1].ch1 || 1, [c0, c1] = prof.range || [0, total], span = Math.max(c1 - c0, 1e-6);
  const vis = rows.filter(r => r.ch1 >= c0 && r.ch0 <= c1);
  let lo = 1e9, hi = -1e9;
  for (const r of vis) for (const v of [r.ground0, r.ground1, r.inv0, r.inv1, r.crown0, r.crown1, r.storm0, r.storm1]) if (v != null) { lo = Math.min(lo, v); hi = Math.max(hi, v); }
  const pad = Math.max((hi - lo) * 0.06, 0.2); lo -= pad; hi += pad;
  if (prof.vz && prof.vz > 1) {                              // level zoom about the middle of what is shown, or about the cursor's level
    const mid = prof.vmid != null ? prof.vmid : (lo + hi) / 2, h = (hi - lo) / prof.vz; lo = mid - h / 2; hi = mid + h / 2;
  }
  const X = c => L + (c - c0) / span * pw, Y = v => T + (hi - v) / (hi - lo) * ph;
  prof.view = { L, T, pw, ph, c0, c1, total, X, Y, W, H, lo, hi };
  let s = `<rect x="${L}" y="${T}" width="${pw}" height="${ph}" fill="#fafbfc" stroke="#d5dbe3"/>`;
  s += `<defs><clipPath id="pclip"><rect x="${L}" y="${T - 20}" width="${pw}" height="${ph + 20}"/></clipPath></defs>`;
  const sx = niceStep(span, Math.max(2, pw / 90)), sy = niceStep(hi - lo, Math.max(2, ph / 36));
  for (let c = Math.ceil(c0 / sx) * sx; c <= c1 + 1e-9; c += sx) s += `<line x1="${X(c)}" x2="${X(c)}" y1="${T}" y2="${T + ph}" stroke="#eef1f5"/><text x="${X(c)}" y="${T + ph + 13}" text-anchor="middle">${+c.toFixed(1)}</text>`;
  for (let v = Math.ceil(lo / sy) * sy; v <= hi; v += sy) s += `<line x1="${L}" x2="${L + pw}" y1="${Y(v)}" y2="${Y(v)}" stroke="#eef1f5"/><text x="${L - 6}" y="${Y(v) + 3}" text-anchor="end">${+v.toFixed(2)}</text>`;
  s += `<text transform="translate(14 ${T + ph / 2}) rotate(-90)" text-anchor="middle">Level (m)</text>`;
  s += `<g clip-path="url(#pclip)">`;
  // ground, and the cover limits under it (crowns below the minimum-cover line, inverts above the maximum)
  const g = [[0, rows[0].ground0]]; for (const r of rows) g.push([r.ch1, r.ground1]);
  const cov = (state.model && state.model.settings && state.model.settings.design) || {};
  const gline = (dz, attrs) => `<polyline points="${g.map(p => `${X(p[0])},${Y(p[1] - dz)}`).join(" ")}" fill="none" ${attrs}/>`;
  s += gline(0, `stroke="#8a6d3b" stroke-width="2"`);
  if (cov.cover_min) s += gline(cov.cover_min, `stroke="#2e9e5b" stroke-width="1" stroke-dasharray="5 3" class="covmin"`);
  if (cov.cover_max && hi - lo > 0 && Math.min(...g.map(p => p[1])) - cov.cover_max > lo) s += gline(cov.cover_max, `stroke="#c0392b" stroke-width="1" stroke-dasharray="5 3" class="covmax"`);
  for (const r of vis) {
    const x0 = X(r.ch0), x1 = X(r.ch1), pump = r.kind === "pump";
    const tip = `${r.link}${pump ? " (pump)" : "  " + szLab(r)}  ${r.slope_pc == null ? "" : num(r.slope_pc, 3) + " %  "}v ${r.v_ms == null ? "-" : num(r.v_ms, 2)} m/s${r.reversed ? "  (walked against the flow)" : ""}`;
    if (pump) { s += `<g class="seg pump" data-link="${esc(r.link)}"><title>${esc(tip)}</title><line class="pipe" x1="${x0}" y1="${Y(r.inv0)}" x2="${x1}" y2="${Y(r.inv1)}" stroke="#7b3fa0" stroke-width="2" stroke-dasharray="5 3"/></g>`; continue; }
    s += `<g class="seg${r.fail ? " fail" : ""}" data-link="${esc(r.link)}"><title>${esc(tip)}</title>` +
      `<polygon points="${x0},${Y(r.inv0)} ${x1},${Y(r.inv1)} ${x1},${Y(r.crown1)} ${x0},${Y(r.crown0)}" fill="${r.fail ? "#f6c9c3" : "#cfe0f5"}" fill-opacity=".75" stroke="${r.fail ? "#d7301f" : "none"}"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.inv0)}" x2="${x1}" y2="${Y(r.inv1)}" stroke="#1f3b73" stroke-width="1.6"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.crown0)}" x2="${x1}" y2="${Y(r.crown1)}" stroke="#4c78b8" stroke-width="1.6"/>` +
      `<line class="pipe" x1="${x0}" y1="${Y(r.water0)}" x2="${x1}" y2="${Y(r.water1)}" stroke="#2a9df4" stroke-width="1.6"/></g>`;
    if (x1 - x0 > 34) {                              // flow direction: the route may walk a pipe against its flow
      const xm = (x0 + x1) / 2, ym = Y((r.crown0 + r.crown1) / 2) - 7, d = r.reversed ? -1 : 1;
      s += `<path d="M${xm - 5 * d},${ym - 3.5} L${xm + 5 * d},${ym} L${xm - 5 * d},${ym + 3.5} Z" fill="${r.reversed ? "#c2410c" : "#4c78b8"}"><title>${r.reversed ? "flow runs right to left here" : "flow"}</title></path>`;
    }
    if (!bands && x1 - x0 > 70) s += `<text x="${(x0 + x1) / 2}" y="${Y((r.inv0 + r.inv1) / 2) + 14}" text-anchor="middle">${esc(szLab(r))}</text>`;
  }
  // manholes as structures; every pipe that meets one off the route drawn where it joins: a circle of its own
  // diameter at its own invert (to the vertical scale), incoming on the upstream side of the shaft, outgoing on the
  // downstream side; a dashed line shows the drop from an incoming invert to the outgoing one
  const stormPts = [[0, rows[0].storm0]].concat(rows.map(r => [r.ch1, r.storm1])).filter(p => p[1] != null);
  if (stormPts.length > 1) s += `<polyline class="storm" points="${stormPts.map(p => `${X(p[0])},${Y(p[1])}`).join(" ")}" fill="none" stroke="#d7301f" stroke-width="1.6" stroke-dasharray="6 3"><title>Peak water level of the last storm run</title></polyline>`;
  const nodes = [{ id: rows[0].from_node, c: 0, gr: rows[0].ground0, iv: rows[0].inv0, ni: rows[0].node_inv0, kind: rows[0].kind0, joins: rows[0].joins0 || [], out: rows[0].inv0, inn: null }];
  rows.forEach((r, k) => nodes.push({ id: r.to_node, c: r.ch1, gr: r.ground1, iv: r.inv1, ni: r.node_inv1, kind: r.kind1, joins: r.joins1 || [],
    out: k + 1 < rows.length ? rows[k + 1].inv0 : null, inn: r.inv1 }));
  prof.view.nodes = nodes;
  const ws = clamp(Math.abs(X(1.2) - X(0)), 3, 26);       // the shaft: a 1.2 m chamber to scale when zoomed in, a symbol when not
  let lastX = -99;
  for (const n of nodes) {
    if (n.c < c0 - 1e-6 || n.c > c1 + 1e-6) continue;
    const x = X(n.c), all = [n.ni, n.iv, n.out, ...n.joins.map(j => j.invert)].filter(v => v != null), bot = Math.min(...all);
    const ww = n.kind === "wetwell" ? ws * 1.8 : ws, stroke = n.kind === "outfall" ? "#123e7c" : n.kind === "wetwell" ? "#7b3fa0" : "#7a8696";
    const fill = n.kind === "wetwell" ? "#efe3f8" : "#ffffff";
    s += `<rect class="mh" data-node="${esc(n.id)}" x="${x - ww / 2}" y="${Y(n.gr)}" width="${ww}" height="${Math.max(1, Y(bot) - Y(n.gr))}" fill="${fill}" fill-opacity=".55" stroke="${stroke}" stroke-width="1.1"><title>${esc(n.id)} (${esc(n.kind || "node")})  ground ${num(n.gr, 2)}  invert ${num(bot, 2)}  depth ${num(n.gr - bot, 2)} m</title></rect>`;
    if (ui.profJoins !== false) {
      let li = 0, lo2 = 0;
      for (const j of n.joins) {
        const D = (j.inside_mm || 0) / 1000, rr = Math.max(3.5, (Y(j.invert) - Y(j.invert + Math.max(D, 0.05))) / 2);
        const side = j.dir === "in" ? -1 : 1, k = j.dir === "in" ? li++ : lo2++;
        const cx = x + side * (ww / 2 + rr + 1 + k * (2 * rr + 2)), cy = Y(j.invert) - rr;
        const ref = n.out != null ? n.out : n.iv, drop = j.dir === "in" && ref != null ? j.invert - ref : null;
        const col = j.kind === "pump" ? "#7b3fa0" : j.dir === "in" ? "#1b9e77" : "#7a8696";
        const tip = `${j.link}${j.kind === "pump" ? " (pump)" : " " + szLab(j)} ${j.dir === "in" ? "joins from" : "leaves to"} ${j.other}` +
          `  invert ${num(j.invert, 2)}` + (drop != null ? `  drop ${num(drop, 2)} m` : "") + (j.q_ls != null ? `  ${num(j.q_ls, 2)} L/s` : "") + (j.transfer ? "  (transfer)" : "");
        if (drop != null && drop > 0.005 && Y(ref) - Y(j.invert) > 3) s += `<line x1="${cx}" x2="${cx}" y1="${Y(j.invert)}" y2="${Y(ref)}" stroke="${col}" stroke-width="1" stroke-dasharray="2 2"/>`;
        s += `<circle class="join" data-link="${esc(j.link)}" cx="${cx}" cy="${cy}" r="${rr}" fill="${col}" fill-opacity=".28" stroke="${col}" stroke-width="1.3"${j.transfer ? ` stroke-dasharray="2 1.5"` : ""}><title>${esc(tip)}</title></circle>`;
      }
    }
    if (x - lastX > 22) { s += `<text class="nlab" data-node="${esc(n.id)}" transform="translate(${x + 3} ${Y(n.gr) - 5}) rotate(-60)">${esc(n.id)}</text>`; lastX = x; }
  }
  s += `</g>`;
  // data bands: per pipe its size, gradient and length; per manhole its ground, invert and depth
  if (bands) {
    const y0 = T + ph + 20, row = k => y0 + 11 + k * 14;
    const hd = ["Pipe", "Ground", "Invert", "Depth"];
    hd.forEach((h, k) => { s += `<text class="bandh" x="${L - 6}" y="${row(k)}" text-anchor="end">${h}</text><line x1="${L}" x2="${L + pw}" y1="${row(k) + 3}" y2="${row(k) + 3}" stroke="#eef1f5"/>`; });
    for (const r of vis) {
      const x0 = Math.max(X(r.ch0), L), x1 = Math.min(X(r.ch1), L + pw), w = x1 - x0;
      const full = r.kind === "pump" ? "pump" : `${szLab(r)} · ${num(r.slope_pc, 2)} % · ${num(r.length_m, 1)} m`, short = r.kind === "pump" ? "P" : r.section ? "sec." : `DN${r.dn_mm}`;
      const t = w > full.length * 5.6 ? full : w > short.length * 6 ? short : "";
      if (t) s += `<text class="band" x="${(x0 + x1) / 2}" y="${row(0)}" text-anchor="middle">${t}</text>`;
    }
    let lx = -99;
    for (const { c, gr, iv } of nodes) {
      if (c < c0 - 1e-6 || c > c1 + 1e-6 || X(c) - lx < 40 || X(c) < L + 18 || X(c) > L + pw - 18) continue; lx = X(c);
      s += `<text class="band" x="${X(c)}" y="${row(1)}" text-anchor="middle">${num(gr, 2)}</text><text class="band" x="${X(c)}" y="${row(2)}" text-anchor="middle">${num(iv, 2)}</text>` +
        `<text class="band" x="${X(c)}" y="${row(3)}" text-anchor="middle">${num(gr - iv, 2)}</text>`;
    }
  }
  // legend and the axis title on the last line
  const lg = [["#8a6d3b", "Ground", ""], ["#1f3b73", "Invert", ""], ["#4c78b8", "Crown", ""], ["#2a9df4", "Water surface", ""]];
  if (cov.cover_min) lg.push(["#2e9e5b", `Min cover ${cov.cover_min} m`, "5 3"]);
  if (ui.profJoins !== false) lg.push(["#1b9e77", "Joining pipe (at its invert)", "o"]);
  if (rows.some(r => r.storm1 != null)) lg.push(["#d7301f", "Storm peak level", "6 3"]);
  let lx = L;
  for (const [c, t, da] of lg) {
    s += da === "o" ? `<circle cx="${lx + 9}" cy="${H - 10}" r="5" fill="${c}" fill-opacity=".28" stroke="${c}" stroke-width="1.3"/>`
                    : `<line x1="${lx}" x2="${lx + 18}" y1="${H - 10}" y2="${H - 10}" stroke="${c}" stroke-width="2.4"${da ? ` stroke-dasharray="${da}"` : ""}/>`;
    s += `<text x="${lx + 24}" y="${H - 6}">${t}</text>`; lx += 24 + t.length * 6.2 + 22;
  }
  s += `<text x="${L + pw}" y="${H - 6}" text-anchor="end">Chainage (m)${prof.range || prof.vz > 1 ? "  ·  wheel: zoom · Shift+wheel or drag: scroll · Ctrl+wheel: levels · double-click: all" : ""}</text>`;
  s += `<g id="prof-cursor" style="display:none"><line y1="${T}" y2="${T + ph}" stroke="#ff7a1a" stroke-width="1.4"/><circle r="3.5" fill="#ff7a1a" data-k="inv"/><circle r="3.5" fill="#2a9df4" data-k="wat"/><circle r="3.5" fill="#8a6d3b" data-k="gnd"/></g>`;
  svg.innerHTML = s;
  if (prof.cursor != null) profCursor(prof.cursor);
  profScrollbar();
}
/* the scrollbar under the profile: the thumb is the part shown; drag it, or click the track to jump */
function profScrollbar() {
  const bar = $("#prof-scroll"), th = $("#prof-thumb"), v = prof.view;
  if (!v || !prof.range) { bar.hidden = true; return; }
  bar.hidden = false;
  th.style.left = (prof.range[0] / v.total * 100) + "%"; th.style.width = Math.max(1.5, (prof.range[1] - prof.range[0]) / v.total * 100) + "%";
  $("#prof-zinfo").textContent = `${num(prof.range[0], 0)}-${num(prof.range[1], 0)} m of ${num(v.total, 0)} m`;
}
function profZoom(k, about) {
  const v = prof.view; if (!v) return;
  const [a, b] = prof.range || [0, v.total], c = about != null ? about : (a + b) / 2;
  let a2 = c - (c - a) * k, b2 = c + (b - c) * k;
  if (b2 - a2 >= v.total * 0.999) prof.range = null;
  else { if (b2 - a2 < 5) return; if (a2 < 0) { b2 -= a2; a2 = 0; } if (b2 > v.total) { a2 -= b2 - v.total; b2 = v.total; } prof.range = [Math.max(0, a2), b2]; }
  renderProfile(prof.rows);
}
function profPan(dc) {
  const v = prof.view; if (!v || !prof.range) return;
  const w = prof.range[1] - prof.range[0], a = clamp(prof.range[0] + dc, 0, Math.max(0, v.total - w));
  prof.range = [a, a + w]; renderProfile(prof.rows);
}
/* the values along the route at chainage c: the pipe there and its levels interpolated */
function profAt(c) {
  const rows = prof.rows; if (!rows || !rows.length) return null;
  let r = rows.find(x => c >= x.ch0 && c <= x.ch1) || (c < rows[0].ch0 ? rows[0] : rows[rows.length - 1]);
  const f = r.ch1 > r.ch0 ? clamp((c - r.ch0) / (r.ch1 - r.ch0), 0, 1) : 0;
  return { r, f, ground: lerp(r.ground0, r.ground1, f), inv: lerp(r.inv0, r.inv1, f), crown: lerp(r.crown0, r.crown1, f), water: lerp(r.water0, r.water1, f) };
}
function profCursor(c) {
  const v = prof.view, el = $("#prof-cursor"), ro = $("#prof-readout");
  if (!v || !el || c == null || c < v.c0 || c > v.c1) { if (el) el.style.display = "none"; ro.hidden = true; return; }
  const a = profAt(c); if (!a) return;
  const x = v.X(c); el.style.display = ""; el.querySelector("line").setAttribute("x1", x); el.querySelector("line").setAttribute("x2", x);
  for (const [k, val] of [["inv", a.inv], ["wat", a.water], ["gnd", a.ground]]) { const ci = el.querySelector(`[data-k=${k}]`); ci.setAttribute("cx", x); ci.setAttribute("cy", val == null ? -99 : v.Y(val)); }
  const r = a.r;
  ro.innerHTML = `<b>${esc(r.link)}</b> ${r.kind === "pump" ? "pump" : esc(szLab(r))}${r.reversed ? " ←" : ""} · ch ${num(c, 1)} m<br>` +
    `ground ${num(a.ground, 2)} · invert ${num(a.inv, 2)} · water ${num(a.water, 2)}<br>` +
    `depth ${num(a.ground - a.inv, 2)} m · cover ${num(a.ground - a.crown, 2)} m` +
    (r.v_ms != null ? `<br>${num(r.q_ls, 2)} L/s · v ${num(r.v_ms, 2)} m/s · d/D ${num(r.d_over_D, 2)}` : "");
  const nd = (v.nodes || []).find(n => Math.abs(v.X(n.c) - x) <= 7);
  if (nd) {
    const ref = nd.out != null ? nd.out : nd.iv, low = Math.min(...[nd.ni, nd.iv, nd.out].filter(q => q != null));
    ro.innerHTML += `<hr><b>${esc(nd.id)}</b> ${esc(nd.kind || "")} · ground ${num(nd.gr, 2)} · depth ${num(nd.gr - low, 2)} m` +
      (nd.inn != null && nd.out != null ? `<br>in ${num(nd.inn, 2)} → out ${num(nd.out, 2)} (fall ${num(nd.inn - nd.out, 3)} m)` : "") +
      nd.joins.map(j => `<br><span style="color:${j.dir === "in" ? "#1b9e77" : "var(--muted)"}">${j.dir === "in" ? "joins" : "leaves"}: ${esc(j.link)} ${j.kind === "pump" ? "pump" : esc(szLab(j))} ${j.dir === "in" ? "from" : "to"} ${esc(j.other)} at ${num(j.invert, 2)}` +
        (j.dir === "in" && ref != null ? ` (drop ${num(j.invert - ref, 2)} m)` : "") + `</span>`).join("");
  }
  ro.hidden = false;
}
/* the route on the map: each link's drawn line in route order, its plan length, and the chainage it spans */
function planDist(a, b) {
  const p = projected({ lng: a[0], lat: a[1] }), q = projected({ lng: b[0], lat: b[1] });
  return p && p.e != null ? Math.hypot(q.e - p.e, q.n - p.n) : new maplibregl.LngLat(...a).distanceTo(new maplibregl.LngLat(...b));
}
function setRoute(rows) {
  prof.segs = []; prof.rows = rows || null;
  const fs = [];
  if (rows && rows.length && state.model) {
    for (const r of rows) {
      const f = state.model.links.get(String(r.link)); if (!f) continue;
      const c = r.reversed ? f.geometry.coordinates.slice().reverse() : f.geometry.coordinates.slice(), cum = [0];
      for (let i = 1; i < c.length; i++) cum.push(cum[i - 1] + planDist(c[i - 1], c[i]));
      prof.segs.push({ r, c, cum, glen: cum[cum.length - 1] || 1e-9 });
      fs.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: c } });
    }
    const mk = (id, lab) => { const n = state.model.nodes.get(String(id)); if (n) fs.push({ type: "Feature", properties: { lab }, geometry: n.geometry }); };
    mk(rows[0].from_node, "S"); mk(rows[rows.length - 1].to_node, "E");
  }
  if (map && map.getSource && map.getSource("route")) map.getSource("route").setData({ type: "FeatureCollection", features: fs });
  setCursor(null);
}
function routePoint(c) {
  const s = prof.segs.find(x => c >= x.r.ch0 && c <= x.r.ch1) || prof.segs[prof.segs.length - 1]; if (!s) return null;
  const f = s.r.ch1 > s.r.ch0 ? clamp((c - s.r.ch0) / (s.r.ch1 - s.r.ch0), 0, 1) : 0, d = f * s.glen;
  for (let i = 1; i < s.c.length; i++) if (s.cum[i] >= d) {
    const t = s.cum[i] > s.cum[i - 1] ? (d - s.cum[i - 1]) / (s.cum[i] - s.cum[i - 1]) : 0;
    return [s.c[i - 1][0] + t * (s.c[i][0] - s.c[i - 1][0]), s.c[i - 1][1] + t * (s.c[i][1] - s.c[i - 1][1])];
  }
  return s.c[s.c.length - 1];
}
function nearestOnRoute(pt) {
  let best = null, bd = 14;
  for (const s of prof.segs) {
    const P = s.c.map(x => map.project(x));
    for (let i = 1; i < P.length; i++) {
      const a = P[i - 1], b = P[i], dx = b.x - a.x, dy = b.y - a.y, L2 = dx * dx + dy * dy;
      const t = L2 ? clamp(((pt.x - a.x) * dx + (pt.y - a.y) * dy) / L2, 0, 1) : 0, d = Math.hypot(a.x + t * dx - pt.x, a.y + t * dy - pt.y);
      if (d < bd) { bd = d; best = s.r.ch0 + (s.cum[i - 1] + t * (s.cum[i] - s.cum[i - 1])) / s.glen * (s.r.ch1 - s.r.ch0); }
    }
  }
  return best;
}
/* one cursor for both views: a marker on the map, a line and a readout on the profile */
function setCursor(c, from) {
  prof.cursor = c; prof.cursorFrom = c == null ? null : from;
  const src = map && map.getSource && map.getSource("cursor"), p = c == null ? null : routePoint(c);
  if (src) src.setData({ type: "FeatureCollection", features: p ? [{ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p } }] : [] });
  profCursor(c);
  if (p && from === "profile" && ui.profFollow && !map.isMoving()) {          // keep the marker in view
    const q = map.project(p), w = map.getCanvas().clientWidth, h = map.getCanvas().clientHeight;
    if (q.x < 40 || q.y < 40 || q.x > w - 40 || q.y > h - 40) map.easeTo({ center: p, duration: 250 });
  }
}
function fitRoute() {
  const pts = prof.segs.flatMap(s => s.c); if (!pts.length) return;
  const b = bboxOf(pts); map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 60, maxZoom: 18, duration: 300 });
}
/* pick a route on the map: each click on a manhole or pipe adds a stop (start, via points, end); Enter finishes */
function startPick() {
  state.routePick = { stops: [] }; $("#prof-pick").classList.add("on"); showTab("profile");
  $("#hint").textContent = "Route: click manholes or pipes in order (start, via points, end). Enter or Pick again to finish.";
}
function finishPick() {
  state.routePick = null; $("#prof-pick").classList.remove("on"); $("#hint").textContent = state.pid ? HINTS[state.tool] : "";
}
function pickStop(id) {
  const st = state.routePick.stops; st.push(id);
  $("#prof-start").value = st[0]; $("#prof-end").value = st.length > 1 ? st[st.length - 1] : "";
  $("#prof-via").value = st.slice(1, -1).join(", ");
  if (st.length > 1) drawProfile(); else $("#prof-msg").textContent = `From ${id}: now click the end, or via points first.`;
}
function profileCsv() {
  const rows = prof.rows || []; if (!rows.length) return;
  const cols = ["link", "kind", "reversed", "from_node", "to_node", "ch0", "ch1", "length_m", "dn_mm", "slope_pc", "ground0", "ground1", "inv0", "inv1", "crown0", "crown1", "water0", "water1", "q_ls", "v_ms", "d_over_D", "fail"];
  const txt = [cols.join(",")].concat(rows.map(r => cols.map(k => r[k] == null ? "" : String(r[k]).includes(",") ? `"${r[k]}"` : r[k]).join(","))).join("\n");
  downloadBlob(new Blob([txt], { type: "text/csv" }), `profile_${rows[0].from_node}_${rows[rows.length - 1].to_node}.csv`);
}
/* the profile as a standalone SVG (styles from the page written into it) or a PNG at twice the size */
function profileSvgText() {
  const svg = $("#profile-svg").cloneNode(true), v = prof.view; if (!v) return null;
  svg.setAttribute("width", v.W); svg.setAttribute("height", v.H); svg.querySelector("#prof-cursor")?.remove();
  const live = $$("#profile-svg text"), ink = getComputedStyle(live[0] || document.body).fill || "#44546a";
  svg.querySelectorAll("text").forEach(t => { t.setAttribute("fill", ink); t.setAttribute("font-family", "system-ui, Segoe UI, sans-serif"); t.setAttribute("font-size", t.classList.contains("band") ? "10" : "10.5"); });
  svg.insertAdjacentHTML("afterbegin", `<rect width="${v.W}" height="${v.H}" fill="${getComputedStyle(document.body).backgroundColor}"/>`);
  return new XMLSerializer().serializeToString(svg);
}
function profileSvg() { const t = profileSvgText(); if (t) downloadBlob(new Blob([t], { type: "image/svg+xml" }), "profile.svg"); }
function profilePng() {
  const t = profileSvgText(), v = prof.view; if (!t) return;
  const img = new Image(), url = URL.createObjectURL(new Blob([t], { type: "image/svg+xml" }));
  img.onload = () => { const c = document.createElement("canvas"); c.width = v.W * 2; c.height = v.H * 2; const g = c.getContext("2d"); g.scale(2, 2); g.drawImage(img, 0, 0); URL.revokeObjectURL(url); c.toBlob(b => downloadBlob(b, "profile.png")); };
  img.src = url;
}
function downloadBlob(blob, name) {
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = name;
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 5000);
}
function wireProfile() {
  const svg = $("#profile-svg");
  const chAt = e => { const v = prof.view; if (!v) return null; const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse()); return v.c0 + (q.x - v.L) / v.pw * (v.c1 - v.c0); };
  svg.addEventListener("mousemove", e => {
    const v = prof.view; if (!v) return;
    if (prof.drag) {                                         // pan along the chainage
      const d = (e.clientX - prof.drag.x) / svg.getBoundingClientRect().width * v.W / v.pw * (prof.drag.r[1] - prof.drag.r[0]);
      if (Math.abs(e.clientX - prof.drag.x) > 3) prof.drag.moved = true;
      const w = prof.drag.r[1] - prof.drag.r[0], a = clamp(prof.drag.r[0] - d, 0, Math.max(0, v.total - w));
      if (prof.drag.moved && prof.range) { prof.range = [a, a + w]; renderProfile(prof.rows); }
      return;
    }
    const c = chAt(e); if (c == null || c < v.c0 || c > v.c1) { setCursor(null); return; }
    setCursor(c, "profile");
    const a = profAt(c); setHot(a ? a.r.link : null);
  });
  svg.addEventListener("mouseleave", () => { prof.drag = null; setCursor(null); setHot(null); });
  svg.addEventListener("wheel", e => {                        // wheel: zoom at the cursor; Shift+wheel or a sideways swipe: scroll along;
    const v = prof.view; if (!v) return; e.preventDefault();  // Ctrl+wheel: zoom the levels
    const [a, b] = prof.range || [0, v.total];
    if (e.ctrlKey) { const p = svg.createSVGPoint(); p.x = e.clientX; p.y = e.clientY; const q = p.matrixTransform(svg.getScreenCTM().inverse());
      const lv = v.hi - (q.y - v.T) / v.ph * (v.hi - v.lo); prof.vmid = lv; prof.vz = clamp((prof.vz || 1) * (e.deltaY > 0 ? 0.8 : 1.25), 1, 40);
      if (prof.vz <= 1.001) { prof.vz = 1; prof.vmid = null; } renderProfile(prof.rows); return; }
    if (e.shiftKey || Math.abs(e.deltaX) > Math.abs(e.deltaY)) { profPan(((e.shiftKey ? e.deltaY : e.deltaX) > 0 ? 1 : -1) * (b - a) * 0.15); return; }
    profZoom(e.deltaY > 0 ? 1.25 : 0.8, chAt(e));
  }, { passive: false });
  $("#prof-zin").onclick = () => profZoom(0.5);
  $("#prof-zout").onclick = () => profZoom(2);
  $("#prof-zall").onclick = () => { prof.range = null; prof.vz = 1; prof.vmid = null; if (prof.rows) renderProfile(prof.rows); };
  const track = $("#prof-scroll"), thumb = $("#prof-thumb");
  thumb.addEventListener("pointerdown", e => {
    e.preventDefault(); e.stopPropagation(); thumb.setPointerCapture(e.pointerId);
    const x0 = e.clientX, r0 = prof.range.slice(), W = track.getBoundingClientRect().width;
    const mv = ev => { const w = r0[1] - r0[0], a = clamp(r0[0] + (ev.clientX - x0) / W * prof.view.total, 0, prof.view.total - w); prof.range = [a, a + w]; renderProfile(prof.rows); };
    const up = () => { thumb.removeEventListener("pointermove", mv); thumb.removeEventListener("pointerup", up); };
    thumb.addEventListener("pointermove", mv); thumb.addEventListener("pointerup", up);
  });
  track.addEventListener("pointerdown", e => {
    if (e.target !== track || !prof.range) return;
    const f = (e.clientX - track.getBoundingClientRect().left) / track.getBoundingClientRect().width, w = prof.range[1] - prof.range[0];
    const a = clamp(f * prof.view.total - w / 2, 0, prof.view.total - w); prof.range = [a, a + w]; renderProfile(prof.rows);
  });
  svg.addEventListener("mousedown", e => { if (e.button === 0 && prof.view) prof.drag = { x: e.clientX, r: prof.range || [0, prof.view.total], moved: false }; });
  addEventListener("mouseup", () => { setTimeout(() => { prof.drag = null; }, 0); });
  svg.addEventListener("dblclick", () => { prof.range = null; prof.vz = 1; prof.vmid = null; if (prof.rows) renderProfile(prof.rows); });
  svg.addEventListener("click", e => {
    if (prof.drag && prof.drag.moved) return;
    const n = e.target.closest(".nlab, .mh"); if (n) { setSel("nodes", [n.dataset.node], { zoom: true, keepProfile: true }); return; }
    const jn = e.target.closest(".join"); if (jn) { setSel("links", [jn.dataset.link], { zoom: true, keepProfile: true }); return; }
    const g = e.target.closest(".seg"); if (g) setSel("links", [g.dataset.link], { zoom: true, keepProfile: true });
  });
  $("#prof-draw").onclick = () => drawProfile();
  for (const id of ["#prof-start", "#prof-end", "#prof-via"]) $(id).addEventListener("keydown", e => { if (e.key === "Enter") drawProfile(); });
  $("#prof-pick").onclick = e => { e.currentTarget.blur(); state.routePick ? finishPick() : startPick(); };
  $("#prof-swap").onclick = () => {
    const rows = prof.rows, s0 = $("#prof-start").value.trim(), e0 = $("#prof-end").value.trim() || (rows && rows.length ? rows[rows.length - 1].to_node : "");
    if (!e0) return;
    $("#prof-start").value = e0; $("#prof-end").value = s0;
    $("#prof-via").value = $("#prof-via").value.split(",").map(x => x.trim()).filter(Boolean).reverse().join(", ");
    drawProfile();
  };
  $("#prof-clear").onclick = () => { for (const id of ["#prof-start", "#prof-end", "#prof-via"]) $(id).value = ""; prof.range = null; $("#profile-svg").innerHTML = ""; $("#prof-msg").textContent = ""; state.lastProfile = null; setRoute(null); finishPick(); };
  $("#prof-bands").checked = ui.profBands;
  $("#prof-bands").onchange = e => { ui.profBands = e.target.checked; saveUi(); if (prof.rows) renderProfile(prof.rows); };
  $("#prof-joins").checked = ui.profJoins !== false;
  $("#prof-joins").onchange = e => { ui.profJoins = e.target.checked; saveUi(); if (prof.rows) renderProfile(prof.rows); };
  $("#prof-follow").checked = ui.profFollow;
  $("#prof-follow").onchange = e => { ui.profFollow = e.target.checked; saveUi(); };
  $("#prof-fit").onclick = fitRoute;
  $("#prof-csv").onclick = profileCsv; $("#prof-svgdl").onclick = profileSvg; $("#prof-png").onclick = profilePng;
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
  state.lastHydro = [ser, label];
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
    `<fieldset><legend>Design limits</legend>${row("design.v_min", "v min (m/s)", "num")}${row("design.v_max", "v max (m/s)", "num")}${row("design.cover_min", "Cover min (m)", "num")}${row("design.cover_max", "Cover max (m)", "num")}${row("self_cleansing_min_dn", "Self-cleansing above DN (mm)", "num")}</fieldset>` +
    SET_TABLES.map(t => tableHtml(t, S)).join("");
  host.insertAdjacentHTML("beforeend", rainHtml());
  host.dataset.sig = state.pid + state.sid; tag(host);
  $$("[data-path]", host).forEach(inp => inp.addEventListener("change", () => {
    let v = inp.value; if (inp.dataset.type === "num") { if (v === "") return; v = Number(v); }
    if (inp.dataset.path === "check_load" && v === "") v = null;
    const path = inp.dataset.path; enqueue(() => exec({ op: "set_setting", path, value: v }));
  }));
  wireRain(host); wireTables(host);
}
/* the project's tables (catalogue, minimum gradient, d/D limit, peaking): edited as a draft, applied as one undoable edit */
const SET_TABLES = [
  { path: "design.catalogue", title: "Pipe catalogue", cols: ["Nominal DN (mm)", "Inside diameter (mm)"], get: S => S.design.catalogue, put: r => r,
    note: "The sizes the design chooses from, smallest first. Pipes already laid keep their own bore." },
  { path: "design.slope_min", title: "Minimum gradient by size", cols: ["From DN (mm)", "Minimum gradient (%)"],
    get: S => Object.entries(S.design.slope_min).map(([k, v]) => [Number(k), +(v * 100).toFixed(5)]).sort((a, b) => a[0] - b[0]),
    put: r => Object.fromEntries(r.map(x => [String(x[0]), x[1] / 100])),
    note: "A size not in the table takes the gradient of the largest tabled size not above it (G203 p29 Table 11)." },
  { path: "design.dd_limits", title: "d/D limit by size", cols: ["Up to DN (mm)", "d/D limit"], get: S => S.design.dd_limits, put: r => r,
    note: "The limit of a size is the first row whose DN it does not exceed (G203 p27 Table 10)." },
  { path: "peaking.table", title: "Peaking factor table", cols: ["Average flow (L/s)", "Peaking factor"], get: S => S.peaking.table, put: r => r,
    note: "Used when the peaking method is 'table'; interpolated between rows." },
];
function tableHtml(t, S) {
  state.tableDraft = state.tableDraft || {};
  const rows = state.tableDraft[t.path] || (t.get(S) || []).map(r => r.slice()), id = t.path.replace(/\./g, "-");
  state.tableDraft[t.path] = rows;
  return `<fieldset class="tbl-set" data-tpath="${t.path}" id="tbl-${id}"><legend>${t.title}</legend><p class="muted small">${t.note}</p>` +
    `<div class="rr muted"><span>${t.cols[0]}</span><span>${t.cols[1]}</span><span></span></div>` +
    rows.map((r, i) => `<div class="rr"><input type="number" step="any" data-i="${i}" data-c="0" value="${r[0] ?? ""}"><input type="number" step="any" data-i="${i}" data-c="1" value="${r[1] ?? ""}"><button data-del="${i}" title="Remove row">&times;</button></div>`).join("") +
    `<div class="row"><button class="tb2" data-act="add">Add row</button><button class="tb2 primary" data-act="apply" data-testid="apply-${id}">Apply</button><button class="tb2" data-act="reset">Reset</button><span class="muted" data-msg></span></div></fieldset>`;
}
function wireTables(host) {
  for (const fs of $$(".tbl-set", host)) {
    const t = SET_TABLES.find(x => x.path === fs.dataset.tpath), rows = state.tableDraft[t.path];
    const redraw = () => { host.dataset.sig = ""; renderSettings(); };
    fs.addEventListener("input", e => { const i = e.target.dataset.i; if (i == null) return; rows[+i][+e.target.dataset.c] = e.target.value === "" ? "" : Number(e.target.value); });
    fs.addEventListener("click", e => {
      const b = e.target.closest("button"); if (!b) return;
      if (b.dataset.del != null) { rows.splice(+b.dataset.del, 1); redraw(); }
      else if (b.dataset.act === "add") { rows.push(["", ""]); redraw(); }
      else if (b.dataset.act === "reset") { delete state.tableDraft[t.path]; redraw(); }
      else if (b.dataset.act === "apply") {
        const ok = rows.filter(r => r[0] !== "" && r[1] !== "" && isFinite(r[0]) && isFinite(r[1])).map(r => [Number(r[0]), Number(r[1])]).sort((a, c) => a[0] - c[0]);
        if (!ok.length) { fs.querySelector("[data-msg]").textContent = "Give at least one complete row."; return; }
        enqueue(async () => {
          await exec({ op: "set_setting", path: t.path, value: t.put(ok) });
          if (t.path === "design.catalogue") state.info.catalogue = ok.map(r => r[0]);           // the size lists follow a new catalogue
          delete state.tableDraft[t.path]; redraw(); toast(`${t.title}: ${ok.length} row${ok.length > 1 ? "s" : ""} applied (undo takes it back).`, "info");
        });
      }
    });
  }
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
  const box = $("#rain-box");                                   // only the rain's rows (the settings tables have their own)
  $$("[data-i]", box).forEach(inp => inp.addEventListener("input", () => { rows()[+inp.dataset.i][+inp.dataset.c] = inp.value === "" ? "" : Number(inp.value); }));
  $$("[data-del]", box).forEach(b => b.onclick = () => { rows().splice(+b.dataset.del, 1); rerender(); });
  $("#rain-apply").onclick = () => {
    R.step_min = Number($("#rain-step").value); R.duration_min = Number($("#rain-duration").value);
    const rs = rows().filter(r => r[0] !== "" && r[1] !== "");
    if (!rs.length) { $("#rain-msg").textContent = "Add at least one row."; return; }
    let rain;
    if (R.mode === "idf") { const s = rs.slice().sort((a, b) => a[0] - b[0]); rain = { step_min: R.step_min, duration_min: R.duration_min, idf: { durations_min: s.map(r => r[0]), intensities: s.map(r => r[1]) } }; }
    else rain = { step_min: R.step_min, series: rs.slice().sort((a, b) => a[0] - b[0]) };
    $("#rain-msg").textContent = "";
    enqueue(async () => { await exec({ op: "set_rain", rain });
      toast(`Rain applied: ${R.mode === "idf" ? "design storm from an IDF table" : "time series"} of ${rs.length} row${rs.length > 1 ? "s" : ""}. Run it with Tools, Run on EPA SWMM 5.`, "info"); });
  };
}

/* ------------------------------------------------------------------ tools menu and tool output */
async function loadToolList() {
  try { state.tools = await jget("/tools"); } catch (e) { state.tools = []; }
  renderToolsMenu();
}
const NOT_IN_MENU = new Set(["assistant", "open_sewergems", "import_gis", "export_dxf", "export_csv"]);          // own tab, own File button, or needs a file
const COMPARE = { name: "compare_stored", menu: "SewerGEMS", label: "Compare with SewerGEMS (stored)", endpoint: "GET /api/g/projects/{pid}/scenarios/{sid}/compare_stored" };
function renderToolsMenu() {
  const host = $("#tools-menu"), groups = {};
  const list = state.tools.filter(t => !NOT_IN_MENU.has(t.name)).concat(state.stored ? [COMPARE] : []);
  for (const t of list) (groups[t.menu || "Tools"] = groups[t.menu || "Tools"] || []).push(t);
  host.innerHTML = Object.entries(groups).map(([g, ts]) => `<div class="mh">${esc(g)}</div>` +
    ts.map(t => `<button data-tool="${esc(t.name)}" data-testid="tool-run-${esc(t.name)}" title="${esc(t.label)}">${esc(t.label.split(/[:(]/)[0].trim())}</button>`).join("")).join("");
  $$("button", host).forEach(b => b.addEventListener("click", () => {
    host.hidden = true;
    if (b.dataset.tool === "design") { openDesignDlg(); return; }                  // scope, preview, then apply
    const t = [...state.tools, COMPARE].find(x => x.name === b.dataset.tool); enqueue(() => runTool(t));
  }));
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
      state.storm = { sid: state.sid, data: r, stale: false }; state.stormFrame = null; stopStormPlay();
      const rows = Object.entries(r.links).map(([id, v]) => ({ id, ...v })).sort((a, b) => (b.capacity_peak || 0) - (a.capacity_peak || 0));
      state.toolout = { tool: t, rows, cols: ["id", "q_peak", "v_peak", "depth_peak", "capacity_peak"], report: { ...r.summary, seconds: r.seconds }, storm: true };
      state.colorBy = "storm_cap"; $("#color-by").value = "storm_cap"; mergeResults();
    } else {
      let rows = r.rows || [], cols;
      if (rows.length && rows[0].id == null) { rows = rows.map((x, k) => ({ id: String(k + 1), ...x })); cols = Object.keys(rows[0]).filter(k => k !== "id"); }
      state.toolout = { tool: t, rows, cols, report: r.report || r.totals || (t.name === "compare_stored" ? r : null), summary: r.summary };
      if (r.scenario) updateScenario(r.scenario);
      if (r.summary && t.name !== "compare_stored") state.summary = r.summary;
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
const REPORT_LABEL = {                      // plain names for the keys a tool returns (the data-k attribute keeps the key)
  pc_flow_within_0_1: "flows within 0.1 % of SewerGEMS (%)", largest_flow_pc: "largest flow difference (%)",
  dv_p05: "velocity difference, 5th percentile (m/s)", dv_p95: "velocity difference, 95th percentile (m/s)",
  q_peak: "peak flow (m³/s)", v_peak: "peak velocity (m/s)", depth_peak: "peak depth (m)", capacity_peak: "peak fullness (depth/height)",
};
function renderToolOut() {
  const o = state.toolout, title = $("#toolout-title"), rep = $("#toolout-report");
  $("#toolout-apply").hidden = !(o && o.apply); $("#toolout-csv").disabled = !(o && o.rows.length);
  if (!o) { title.textContent = "No tool run yet. Use the Tools menu."; rep.innerHTML = ""; $("#tbl-toolout").innerHTML = ""; return; }
  title.textContent = o.tool.label;
  let h = "";
  if (o.report) {
    const r = o.report, flat = [];
    const walk = (obj, pre) => { for (const [k, v] of Object.entries(obj)) { if (k === "sizes") continue; if (v && typeof v === "object" && !Array.isArray(v)) walk(v, pre + k + "."); else flat.push([pre + k, v]); } };
    walk(r, "");
    h += `<div class="kv" data-testid="${o.storm ? "storm-report" : "design-report"}">` + flat.map(([k, v]) => `<span>${esc(REPORT_LABEL[k] || k.replace(/_/g, " "))}: <b data-k="${esc(k)}">${esc(typeof v === "number" ? +v.toFixed(4) : Array.isArray(v) ? v.join(", ") : v)}</b></span>`).join("") + `</div>`;
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
    $("#asst-status").textContent = on ? "available (the model is chosen on the right)" : `not available: ${s.reason}`;
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
  const body = { project: state.pid, scenario: state.sid, message: text, history: state.history.slice(), model: $("#asst-model").value,
                 selection: state.sel.ids.length ? { table: state.sel.table, ids: state.sel.ids.slice(0, 500) } : null,
                 route: $("#prof-start").value.trim() ? { start: $("#prof-start").value.trim(), end: $("#prof-end").value.trim(), via: $("#prof-via").value.trim() } : null };
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
      for (const a of r.ui_actions || []) {                          // what it pointed at: selected and zoomed, or a profile drawn
        if (a.kind === "select") { setSel(a.table, a.ids, { zoom: true }); wait.insertAdjacentHTML("beforeend", `<div class="tc" data-testid="asst-action">shown on the map: ${a.ids.length} ${esc(a.table)}</div>`); }
        else if (a.kind === "profile") { $("#prof-start").value = a.start; $("#prof-end").value = a.end || ""; $("#prof-via").value = a.via || ""; await drawProfile();
          wait.insertAdjacentHTML("beforeend", `<div class="tc" data-testid="asst-action">profile drawn from ${esc(a.start)} (Profile tab)</div>`); }
      }
    } catch (e) { wait.className = "msg err"; wait.textContent = e.message; }
    finally { document.body.dataset.asstBusy = "0"; if (state.asstOn) { inp.disabled = $("#asst-send").disabled = false; } $("#asst-log").scrollTop = $("#asst-log").scrollHeight; }
  });
}

/* ------------------------------------------------------------------ tabs */
function showTab(t) {
  setTimeout(saveSession, 0);
  if (ui.bottomCollapsed) setBottom(false);
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
  else if (t === "summary") renderSummary();
  else if (t === "hydro") drawHydro();
  else if (t === "profile") { if (!$("#prof-start").value) autoProfile(); else drawProfile(true); }
}

/* ------------------------------------------------------------------ project actions */
async function openProject(info, fit = true) {
  state.pid = info.id; state.info = info; state.sid = "base"; state.sel = { table: null, ids: [] }; state.pipeStart = null;
  state.toolout = null; state.results = null; state.summary = null; state.storm = null; state.draw = null; state.catchPending = null;
  state.rain = { step_min: 5, duration_min: 60, mode: "idf", idf: [], series: [] }; state.rainSig = null; state.history = [];
  state.source = "engine"; state.stored = null; state.storedCache = {}; $("#results-source").value = "engine";
  $("#asst-log").innerHTML = "";
  if (state.colorBy.startsWith("storm")) { state.colorBy = "v_ms"; $("#color-by").value = "v_ms"; }
  state.tableDraft = {}; $("#prof-start").value = ""; $("#prof-end").value = ""; $("#prof-via").value = ""; prof.range = null; setRoute(null); if (state.routePick) finishPick(); $("#settings-form").dataset.sig = "";
  await mapReady;
  applyBasemap(); clearMeasure();
  await loadToolList();
  await refreshAll(true);
  if (!state.model.nodeFeat.length && !info.basemap) map.jumpTo({ center: [150 / M_LON, 100 / M_LAT], zoom: 17 });
  updateGrid(); setTool(state.tool);
  await loadRefs(); state.trace = null; clearCompare(); state.stormFrame = null; stopStormPlay(); await loadRoutes(); saveSession();
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
/* ---- SewerGEMS: open an export, or export any model from the shared folders through the VM bridge (SewerGEMS's own
   API reads it there, from a copy); the jobs' progress is followed here and the export opens when it is ready */
let sgData = null, sgTimer = null;
async function openSgDlg() {
  const list = $("#sg-list"); list.innerHTML = "Loading..."; $("#dlg-sg").hidden = false;
  await refreshSg(); sgPoll();
}
async function refreshSg() {
  try { sgData = await jget("/sewergems/models"); } catch (e) { $("#sg-list").textContent = e.message; return; }
  const d = sgData, w = d.watcher, list = $("#sg-list");
  $("#sg-watch").innerHTML = w.alive ? `<span class="ok">&#9679;</span> The VM bridge is running${w.busy ? " (busy with a job)" : ""}.`
    : `<span class="bad">&#9679;</span> The VM bridge is not running: ${esc(w.reason || "")}. Exports wait in the queue until it runs.`;
  list.innerHTML = d.exports.length ? d.exports.map(e => `<button data-name="${esc(e.name)}" id="sg-${esc(e.name)}">${esc(e.name)} (${e.scenarios} scenarios)</button>`).join("")
    : `<p data-testid="sg-empty" class="muted">No exports yet: export a model below.</p>`;
  tag(list);
  renderSgModels(); renderSgJobs();
}
function openSgExport(name) {
  const crs = Number($("#sg-crs").value) || null;
  $("#dlg-sg").hidden = true;
  enqueue(() => withBusy(`Opening ${name} (all scenarios)...`, async () => openProject(await jpost(`/projects/open_sewergems/${encodeURIComponent(name)}${crs ? `?crs=${crs}` : ""}`))));
}
function renderSgModels() {
  const q = ($("#sg-filter").value || "").toLowerCase(), host = $("#sg-models"), d = sgData; if (!d) return;
  const ms = d.models.filter(m => !q || (m.folder + " " + m.name).toLowerCase().includes(q));
  host.innerHTML = ms.length ? ms.map(m => `<div class="sgm" data-guest="${esc(m.guest)}" data-tag="${esc(m.tag)}"><span class="nm" title="${esc(m.guest)}"><b>${esc(m.name)}</b> <span class="muted">${esc(m.folder)}</span></span>` +
      `<span class="muted">${m.mb != null ? m.mb + " MB" : ""}</span><span class="muted">${esc(m.modified)}</span>` +
      (m.exported ? `<button data-act="open">Open</button>` : `<button data-act="export">Export</button>`) + `</div>`).join("")
    : `<p class="muted">No SewerGEMS model (.stsw) in ${d.shares.map(esc).join(" or ")}${q ? " matches the filter" : ""}.</p>`;
  tag(host);
}
function renderSgJobs() {
  const d = sgData; if (!d) return;
  const lab = { queued: "waiting for the VM", running: "SewerGEMS is exporting", ready: "ready", failed: "failed", done: "finished", unknown: "?" };
  $("#sg-jobs").innerHTML = d.jobs.length ? `<h4>Exports</h4>` + d.jobs.slice(0, 6).map(j => `<div class="sgj ${j.state}" data-tag="${esc(j.tag)}"><b>${esc(j.tag)}</b> <span>${lab[j.state] || j.state}` +
      (j.state === "running" ? ` (${j.scenarios_done} scenarios so far, ${j.seconds ?? 0} s)` : "") + `</span>` +
      (j.state === "ready" ? `<button data-act="open">Open</button>` : "") + (j.error ? `<div class="errtxt">${esc(j.error.slice(0, 300))}</div>` : "") + `</div>`).join("") : "";
}
function sgPoll() {
  clearInterval(sgTimer);
  const active = () => sgData && sgData.jobs.some(j => j.state === "queued" || j.state === "running");
  if (!active()) return;
  sgTimer = setInterval(async () => {
    const before = new Map(sgData.jobs.map(j => [j.job, j.state]));
    await refreshSg();
    for (const j of sgData.jobs) if (before.get(j.job) && before.get(j.job) !== j.state && (j.state === "ready" || j.state === "failed"))
      toast(j.state === "ready" ? `${j.tag} is exported: File > Open SewerGEMS model to open it.` : `The export of ${j.tag} failed (see the dialog).`, j.state === "ready" ? "info" : "err");
    if (!active()) clearInterval(sgTimer);
  }, 3000);
}
async function sgExport(guest, tag) {
  try { await jpost("/sewergems/export", { guest, tag, run: $("#sg-run").checked }); } catch (e) { toast(e.message); return; }
  toast(`Export of ${tag || guest} queued for the VM; it takes from seconds to several minutes, by the model's size and scenarios.`, "info");
  await refreshSg(); sgPoll();
}
/* ---- import from GIS layers: two files, a field mapping for each, a snap tolerance */
const GIS_FIELDS = {
  nodes: ["id", "kind", "ground", "invert"],
  links: ["id", "from_node", "to_node", "dn_mm", "inside_mm", "up_inv", "dn_inv", "length_m"],
};
const gisFiles = { nodes: null, links: null };
function gisUpdate() { $("#gis-import").disabled = !(gisFiles.nodes && gisFiles.links); }
async function gisPick(kind, file) {
  gisFiles[kind] = null; $("#gis-error").textContent = ""; const info = $(`#gis-${kind}-info`), grid = $(`#gis-${kind}-map`);
  if (!file) { info.textContent = ""; grid.innerHTML = ""; gisUpdate(); return; }
  info.textContent = "Reading..."; grid.innerHTML = "";
  try {
    const fd = new FormData(); fd.append("file", file);
    const r = await (await api("/gis/fields", { method: "POST", body: fd })).json();
    gisFiles[kind] = file;
    info.textContent = `${r.rows} rows, ${r.geometry || "geometry"}, ${r.crs ? "EPSG:" + r.crs : "no CRS"}`;
    const opts = `<option value="">(none)</option>` + r.fields.map(f => `<option>${esc(f)}</option>`).join("");
    grid.innerHTML = GIS_FIELDS[kind].map(f => `<label for="gis-map-${kind}-${f}">${f}</label><select id="gis-map-${kind}-${f}" data-field="${f}">${opts}</select>`).join("");
    for (const sel of $$("select", grid)) { const hit = r.fields.find(x => x.toLowerCase() === sel.dataset.field.toLowerCase()); if (hit) sel.value = hit; }
    tag(grid);
  } catch (e) { info.textContent = ""; $("#gis-error").textContent = e.message; }
  gisUpdate();
}
function gisMapping() {
  const m = { nodes: {}, links: {} };
  for (const kind of ["nodes", "links"]) for (const sel of $$(`#gis-${kind}-map select`)) if (sel.value) m[kind][sel.dataset.field] = sel.value;
  return m;
}
function openGisDlg() {
  gisFiles.nodes = gisFiles.links = null; $("#gis-nodes-file").value = ""; $("#gis-links-file").value = "";
  for (const k of ["nodes", "links"]) { $(`#gis-${k}-info`).textContent = ""; $(`#gis-${k}-map`).innerHTML = ""; }
  $("#gis-error").textContent = ""; gisUpdate(); $("#dlg-gis").hidden = false;
}
async function gisImport() {
  const q = new URLSearchParams({ mapping: JSON.stringify(gisMapping()), snap_m: $("#gis-snap").value || "1", name: $("#gis-name").value || "Imported network" });
  const fd = new FormData(); fd.append("nodes", gisFiles.nodes); fd.append("links", gisFiles.links);
  $("#gis-error").textContent = ""; busy(true, "Importing...");
  try {
    const info = await (await api(`/projects/import_gis?${q}`, { method: "POST", body: fd })).json();
    $("#dlg-gis").hidden = true; await openProject(info);
  } catch (e) { $("#gis-error").textContent = e.message; }
  finally { busy(false); }
}
function wireUi() {
  $("#file-btn").onclick = e => { e.stopPropagation(); $("#file-menu").hidden = !$("#file-menu").hidden; };
  $("#gis-btn").onclick = openGisDlg; $("#gis-cancel").onclick = () => { $("#dlg-gis").hidden = true; };
  $("#gis-nodes-file").onchange = e => gisPick("nodes", e.target.files[0]);
  $("#gis-links-file").onchange = e => gisPick("links", e.target.files[0]);
  $("#gis-import").onclick = () => enqueue(gisImport);
  $("#export-dxf-btn").onclick = () => enqueue(async () => { if (state.pid) saveBlob(await api(`/projects/${state.pid}/export.dxf?sid=${encodeURIComponent(state.sid)}`), "network.dxf"); });
  $("#export-csv-btn").onclick = () => enqueue(async () => { if (state.pid) saveBlob(await api(`/projects/${state.pid}/export.csv?sid=${encodeURIComponent(state.sid)}`), "links.csv"); });
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
  $("#scenario-select").onchange = e => enqueue(() => switchScenario(e.target.value));
  $("#copy-btn").onclick = () => enqueue(async () => {
    const r = await jpost(`${base()}/copy`, {}); state.info = r; state.sid = r.created; $("#settings-form").dataset.sig = ""; await refreshAll(false);
  });
  const hist = which => enqueue(async () => {
    const r = await jpost(`${base()}/${which}`); updateScenario(r.scenario); state.summary = r.summary;
    await loadModel(); await loadResults(); renderAll();
  });
  $("#undo-btn").onclick = () => hist("undo"); $("#redo-btn").onclick = () => hist("redo");
  $("#tools-btn").onclick = e => { e.stopPropagation(); $("#tools-menu").hidden = !$("#tools-menu").hidden; };
  document.addEventListener("click", () => { $("#tools-menu").hidden = true; $("#file-menu").hidden = true; });
  $("#color-by").onchange = e => { state.colorBy = e.target.value; mergeResults(); renderLegend(); pushMap(); stormBar(); if (state.stormFrame) enqueue(() => loadFrame(state.stormFrame.period)); };
  wireView();
  $$(".tool").forEach(b => b.addEventListener("click", () => setTool(b.id.slice(5))));
  $$(".tab").forEach(b => b.addEventListener("click", () => showTab(b.id.slice(4))));
  $("#hydro-attr").onchange = drawHydro;
  $("#results-source").onchange = e => enqueue(async () => { state.source = e.target.value; mergeResults(); renderAll(); });
  $("#sg-btn").onclick = openSgDlg; $("#sg-cancel").onclick = () => { $("#dlg-sg").hidden = true; };
  $("#sg-list").addEventListener("click", e => { const b = e.target.closest("button[data-name]"); if (b) openSgExport(b.dataset.name); });
  $("#sg-filter").addEventListener("input", renderSgModels);
  $("#sg-models").addEventListener("click", e => {
    const b = e.target.closest("button[data-act]"); if (!b) return; const row = b.closest(".sgm");
    if (b.dataset.act === "open") openSgExport(row.dataset.tag); else sgExport(row.dataset.guest, row.dataset.tag);
  });
  $("#sg-jobs").addEventListener("click", e => { const b = e.target.closest("button[data-act=open]"); if (b) openSgExport(b.closest(".sgj").dataset.tag); });
  $("#sg-export-path").onclick = () => { const g = $("#sg-guest").value.trim(); if (g) sgExport(g, null); };
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
  document.addEventListener("keydown", e => {
    if (e.key === "F2") { e.preventDefault(); setProps(!ui.propsCollapsed); return; }
    if (e.key === "F3") { e.preventDefault(); setBottom(!ui.bottomCollapsed); return; }
    if (e.key === "F4") { e.preventDefault(); toggleMapOnly(); return; }
    if (e.ctrlKey && e.key.toLowerCase() === "f") { e.preventDefault(); $("#find-input").focus(); $("#find-input").select(); return; }
    const tg = e.target.tagName; if (["INPUT", "SELECT", "TEXTAREA"].includes(tg)) return;
    const k = e.key.toLowerCase();
    if (state.routePick && (k === "enter" || k === "escape")) { e.preventDefault(); finishPick(); return; }
    if (k === "/") { e.preventDefault(); $("#find-input").focus(); return; }
    if (e.key === "?") { $("#dlg-keys").hidden = !$("#dlg-keys").hidden; return; }
    if (!e.ctrlKey && k === "h" && state.model) { fitModel(); return; }
    if (!e.ctrlKey && k === "z" && state.sel.ids.length) { zoomTo(state.sel.table, state.sel.ids); return; }
    if (!e.ctrlKey && k === "r" && state.pid) { setTool("measure"); return; }
    if (!e.ctrlKey && (k === "u" || k === "d") && state.sel.ids.length) { trace(k === "u" ? "up" : "down"); return; }
    if (e.ctrlKey && k === "z") { e.preventDefault(); $("#undo-btn").click(); }
    else if (e.ctrlKey && k === "y") { e.preventDefault(); $("#redo-btn").click(); }
    else if (k === "enter" && state.tool === "catchment") finishCatchment();
    else if (k === "escape") { clearMeasure(); state.pipeStart = null; state.movePick = null; if (state.tool === "catchment") setTool("catchment"); setSel(null, []); $("#hint").textContent = state.pid ? HINTS[state.tool] : ""; highlight(); }
    else if (k === "delete" && state.sel.ids.length) { const t = state.sel.table, ids = state.sel.ids.slice(); enqueue(() => deleteIds(t, ids)); }
    else if (!e.ctrlKey) { const m = { s: "select", m: "manhole", o: "outfall", w: "wetwell", p: "pipe", v: "move", c: "catchment" }[k]; if (m) setTool(m); }
  });
}

/* ------------------------------------------------------------------ view: panels, theme, basemaps, find, readouts */
const UI_KEY = "w19.ui";
const ui = (() => {
  const d = { pw: 320, bh: 260, propsCollapsed: false, bottomCollapsed: false, toolsCompact: false, mapOnly: null,
              theme: "light", basemap: "osm", prevBasemap: "osm", opacity: 1, labels: true, hillshade: false, arrows: true, cardFolded: false, profBands: true, profFollow: true, profJoins: true, showFail: true };
  try { return Object.assign(d, JSON.parse(localStorage.getItem(UI_KEY) || "{}")); } catch (e) { return d; }
})();
function saveUi() { try { localStorage.setItem(UI_KEY, JSON.stringify(ui)); } catch (e) { /* private window: sizes are not kept */ } }
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function applyPanels() {
  const b = document.body;
  ui.pw = clamp(ui.pw, 220, Math.max(240, innerWidth * 0.5)); ui.bh = clamp(ui.bh, 120, Math.max(140, innerHeight * 0.75));
  b.style.setProperty("--pw", ui.pw + "px"); b.style.setProperty("--bh", ui.bh + "px");
  b.classList.toggle("props-collapsed", ui.propsCollapsed); b.classList.toggle("bottom-collapsed", ui.bottomCollapsed);
  b.classList.toggle("tools-compact", ui.toolsCompact);
  $("#props-btn").classList.toggle("on", !ui.propsCollapsed); $("#bottom-btn").classList.toggle("on", !ui.bottomCollapsed);
  $("#tools-compact-btn").classList.toggle("on", !ui.toolsCompact); $("#maxmap-btn").classList.toggle("on", !!ui.mapOnly);
  $("#display-card").classList.toggle("folded", ui.cardFolded);
  saveUi();
}
function setProps(collapsed) { ui.propsCollapsed = collapsed; ui.mapOnly = null; applyPanels(); }
function setBottom(collapsed) { ui.bottomCollapsed = collapsed; ui.mapOnly = null; applyPanels(); if (!collapsed) requestAnimationFrame(redrawCharts); }
function toggleMapOnly() {
  if (ui.mapOnly) { const m = ui.mapOnly; ui.propsCollapsed = m.p; ui.bottomCollapsed = m.b; ui.mapOnly = null; }
  else { ui.mapOnly = { p: ui.propsCollapsed, b: ui.bottomCollapsed }; ui.propsCollapsed = ui.bottomCollapsed = true; }
  applyPanels();
}
/* drag a splitter: pointer capture, the size set once per frame; dragged nearly shut it collapses; double-click toggles */
function splitter(el, axis) {
  let raf = 0;
  el.addEventListener("pointerdown", ev => {
    if (ev.button !== 0) return;
    ev.preventDefault(); el.setPointerCapture(ev.pointerId); el.classList.add("drag"); document.body.classList.add("resizing");
    const move = e => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        if (axis === "v") { const w = innerWidth - e.clientX - 3; ui.propsCollapsed = w < 150; if (!ui.propsCollapsed) ui.pw = w; }
        else { const h = innerHeight - e.clientY - 3; ui.bottomCollapsed = h < 80; if (!ui.bottomCollapsed) ui.bh = h; }
        ui.mapOnly = null; applyPanels();
      });
    };
    const up = () => { el.releasePointerCapture(ev.pointerId); el.classList.remove("drag"); document.body.classList.remove("resizing");
      el.removeEventListener("pointermove", move); el.removeEventListener("pointerup", up); redrawCharts(); };
    el.addEventListener("pointermove", move); el.addEventListener("pointerup", up);
  });
  el.addEventListener("dblclick", () => axis === "v" ? setProps(!ui.propsCollapsed) : setBottom(!ui.bottomCollapsed));
}
let chartT = 0;
function redrawCharts() {
  clearTimeout(chartT);
  chartT = setTimeout(() => {
    if (state.tab === "profile" && state.lastProfile) renderProfile(state.lastProfile);
    if (state.tab === "hydro" && state.lastHydro) renderHydro(...state.lastHydro);
  }, 80);
}
/* basemap, opacity, satellite labels, hillshade, arrows; only for projects in a real CRS */
function applyBasemap() {
  if (!map || !map.getLayer || !map.getLayer("bm-osm")) return;
  const on = !!(state.info && state.info.basemap), bm = ui.basemap;
  for (const k of Object.keys(BASEMAPS)) map.setLayoutProperty("bm-" + k, "visibility", on && bm === k ? "visible" : "none");
  if (on && BASEMAPS[bm]) map.setPaintProperty("bm-" + bm, "raster-opacity", +ui.opacity);
  for (const k of ["sat-labels", "sat-roads"]) map.setLayoutProperty(k, "visibility", on && bm === "sat" && ui.labels ? "visible" : "none");
  map.setLayoutProperty("hillshade", "visibility", on && ui.hillshade ? "visible" : "none");
  for (const k of ["links-arrow", "links-label"]) map.setLayoutProperty(k, "visibility", ui.arrows ? "visible" : "none");
  map.setLayoutProperty("links-fail", "visibility", ui.showFail ? "visible" : "none");
  $("#fail-toggle").checked = ui.showFail;
  // on imagery or a dark map the pipes need a dark casing and light labels
  const darkUnder = on && (bm === "sat" || bm === "dark") || ui.theme === "dark" && (!on || bm === "none");
  map.setPaintProperty("links-casing", "line-color", darkUnder ? "#0b1118" : "#ffffff");
  map.setPaintProperty("links-casing", "line-opacity", bm === "sat" && on ? 0.55 : 0.75);
  for (const [l, p] of [["links-label", "text"], ["nodes-label", "text"]]) {
    map.setPaintProperty(l, p + "-color", darkUnder ? "#f1f5f9" : "#1d2733"); map.setPaintProperty(l, p + "-halo-color", darkUnder ? "#0b1118" : "#ffffff");
  }
  map.setPaintProperty("links-arrow", "icon-color", darkUnder ? "#f1f5f9" : "#1d2733");
  $("#basemap-select").value = bm; $("#basemap-opacity").value = ui.opacity;
  $("#labels-toggle").checked = ui.labels; $("#hillshade-toggle").checked = ui.hillshade; $("#arrows-toggle").checked = ui.arrows;
  $("#labels-toggle").disabled = bm !== "sat";
}
function applyTheme() {
  document.body.classList.toggle("dark", ui.theme === "dark");
  if (map && map.getLayer && map.getLayer("bg")) {
    map.setPaintProperty("bg", "background-color", ui.theme === "dark" ? "#0e1319" : "#f3f5f8");
    map.setPaintProperty("grid", "line-color", ui.theme === "dark" ? "#253140" : "#d6dde6");
  }
  applyBasemap(); if (state.lastProfile) redrawCharts();
}
function setTheme(t) {
  ui.theme = t;
  if (t === "dark" && (ui.basemap === "osm" || ui.basemap === "light")) { ui.prevBasemap = ui.basemap; ui.basemap = "dark"; }
  else if (t === "light" && ui.basemap === "dark") ui.basemap = ui.prevBasemap || "osm";
  saveUi(); applyTheme();
}
/* a small arrow drawn on a canvas, tinted by icon-color (SDF), placed along each pipe in its from -> to direction */
function arrowImage() {
  const c = document.createElement("canvas"); c.width = 24; c.height = 24; const g = c.getContext("2d");
  g.fillStyle = "#000"; g.beginPath(); g.moveTo(5, 5); g.lineTo(20, 12); g.lineTo(5, 19); g.lineTo(9, 12); g.closePath(); g.fill();
  return g.getImageData(0, 0, 24, 24);
}
/* coordinates under the cursor in the project's own system: UTM (WGS 84 zones, EPSG 326xx/327xx) computed here,
   local metres from the plane mapping, otherwise longitude/latitude */
function utm(lon, lat, zone, south) {
  const a = 6378137, f = 1 / 298.257223563, k0 = 0.9996, e2 = f * (2 - f), ep2 = e2 / (1 - e2), d = Math.PI / 180;
  const phi = lat * d, lam0 = ((zone - 1) * 6 - 180 + 3) * d, s = Math.sin(phi), c = Math.cos(phi), t = Math.tan(phi);
  const N = a / Math.sqrt(1 - e2 * s * s), T = t * t, C = ep2 * c * c, A = c * (lon * d - lam0);
  const M = a * ((1 - e2 / 4 - 3 * e2 ** 2 / 64 - 5 * e2 ** 3 / 256) * phi - (3 * e2 / 8 + 3 * e2 ** 2 / 32 + 45 * e2 ** 3 / 1024) * Math.sin(2 * phi)
    + (15 * e2 ** 2 / 256 + 45 * e2 ** 3 / 1024) * Math.sin(4 * phi) - (35 * e2 ** 3 / 3072) * Math.sin(6 * phi));
  const x = k0 * N * (A + (1 - T + C) * A ** 3 / 6 + (5 - 18 * T + T * T + 72 * C - 58 * ep2) * A ** 5 / 120) + 500000;
  let y = k0 * (M + N * t * (A * A / 2 + (5 - T + 9 * C + 4 * C * C) * A ** 4 / 24 + (61 - 58 * T + T * T + 600 * C - 330 * ep2) * A ** 6 / 720));
  if (south) y += 10000000;
  return [x, y];
}
function projected(ll) {
  const crs = state.info && state.info.crs;
  if (!state.info) return null;
  if (!crs) return { e: ll.lng * M_LON, n: ll.lat * M_LAT, unit: "m" };
  if ((crs > 32600 && crs <= 32660) || (crs > 32700 && crs <= 32760)) { const [e, n] = utm(ll.lng, ll.lat, crs % 100, crs > 32700); return { e, n, unit: "m" }; }
  return { lon: ll.lng, lat: ll.lat };
}
let lastLL = null;
function showCoords(ll) {
  ll = ll || lastLL; const el = $("#coords"); if (!ll || !state.info) { el.textContent = ""; return; } lastLL = ll;
  const p = projected(ll), z = map.getZoom().toFixed(1), fmt = v => v.toLocaleString("en-US", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
  el.textContent = p.e != null ? `E ${fmt(p.e)}  N ${fmt(p.n)}  z ${z}` : `${p.lat.toFixed(6)}, ${p.lon.toFixed(6)}  z ${z}`;
}
/* hover: coordinates always; a tooltip with the element's key values under the Select tool; the profile segment lit */
let hoverRaf = 0, hotId = null;
function hover(e) {
  cancelAnimationFrame(hoverRaf);
  hoverRaf = requestAnimationFrame(() => {
    showCoords(e.lngLat);
    if (prof.segs.length && !dragging) {                    // near the profiled route: the profile shows where the cursor is
      const c = nearestOnRoute(e.point);
      if (c != null) setCursor(c, "map"); else if (prof.cursorFrom === "map") setCursor(null);
    }
    const tip = $("#maptip");
    if (!state.model || dragging || !["select", "delete"].includes(state.tool)) { tip.hidden = true; return; }
    const p = e.point, box = [[p.x - 5, p.y - 5], [p.x + 5, p.y + 5]];
    const fs = map.queryRenderedFeatures(box, { layers: ["nodes", "links-base"] });
    const node = fs.find(f => f.layer.id === "nodes" && (f.properties.kind !== "manhole" || map.getZoom() >= 14.5)), link = fs.find(f => f.layer.id === "links-base");
    let h = "";
    if (node) {
      const q = node.properties, dep = q.ground != null && q.invert != null ? (q.ground - q.invert) : null;
      h = `<b>${esc(q.id)}</b> · ${esc(q.kind)} · ground ${num(q.ground, 2)} · invert ${num(q.invert, 2)}` + (dep != null ? ` · depth ${num(dep, 2)} m` : "");
      setHot(null);
    } else if (link) {
      const q = link.properties, r = srcLinks()[q.id] || {}, en = (state.results && state.results.links[q.id]) || {};
      h = `<b>${esc(q.id)}</b> · ${q.kind === "pump" ? "pump" : q.section ? "section " + esc(q.section) + (q.sec ? "" : " (not analysed)") : "DN" + esc(q.dn_mm)}` + (en.s_pc != null ? ` · ${num(en.s_pc, 3)} %` : "") +
        (r.q_ls != null ? ` · ${num(r.q_ls, 2)} L/s` : "") + (r.v_ms != null ? ` · v ${num(r.v_ms, 2)} m/s` : "") + (r.d_over_D != null ? ` · d/D ${num(r.d_over_D, 2)}` : "") +
        (q._fail ? ` · <span style="color:var(--bad)">failing</span>` : "");
      setHot(q.id);
    } else { setHot(null); h = refFeatureTip(p); }
    if (!h) { tip.hidden = true; return; }
    tip.innerHTML = h; tip.hidden = false;
    const W = $("#map-wrap").clientWidth, tw = tip.offsetWidth;
    tip.style.left = Math.min(p.x + 14, W - tw - 6) + "px"; tip.style.top = (p.y + 16) + "px";
  });
}
function setHot(id) {
  if (id === hotId) return; hotId = id;
  const s = map.getSource && map.getSource("hot"), f = id && state.model && state.model.links.get(String(id));
  if (s) s.setData({ type: "FeatureCollection", features: f ? [f] : [] });
  $$("#profile-svg .seg").forEach(g => g.classList.toggle("hot", g.dataset.link === id));
}
/* find an element by ID: exact, then ignoring case, then the first that starts with the text */
function findElement(text) {
  const q = text.trim(); if (!q || !state.model) return;
  const tables = ["nodes", "links", "catchments"], lq = q.toLowerCase();
  let hit = null;
  for (const t of tables) if (tmap(t).has(q)) { hit = [t, q]; break; }
  if (!hit) for (const t of tables) { for (const k of tmap(t).keys()) if (k.toLowerCase() === lq) { hit = [t, k]; break; } if (hit) break; }
  if (!hit) for (const t of tables) { for (const k of tmap(t).keys()) if (k.toLowerCase().startsWith(lq)) { hit = [t, k]; break; } if (hit) break; }
  if (!hit) { toast(`No node, link or catchment with ID "${q}".`); return; }
  setSel(hit[0], [hit[1]], { zoom: true });
  $("#find-input").value = hit[1];
}
/* the status line's failing counts: each click selects and zooms to the next pipe with that flag */
const FLAG_NAME = { over_limit: "over the d/D limit", over_vmax: "over v max", surcharged: "surcharged", negative_slope: "flat or adverse" };
function stepFailure(flag) {
  const E = state.results ? state.results.links : {};
  const ids = Object.keys(E).filter(k => E[k][flag]).sort((a, b) => a.localeCompare(b, undefined, { numeric: true }));
  if (!ids.length) return;
  const i = state.failStep && state.failStep.flag === flag ? (state.failStep.i + 1) % ids.length : 0;
  state.failStep = { flag, i };
  setSel("links", [ids[i]], { zoom: true });
  toast(`${ids[i]}: ${i + 1} of ${ids.length} ${FLAG_NAME[flag]}. Click the count again for the next.`, "info");
}
/* measure: a route of clicked points, its length on the ground */
function addMeasure(ll) {
  state.measure = (state.measure || []).concat([[ll.lng, ll.lat]]); drawMeasure();
}
function clearMeasure() {
  state.measure = []; if (map && map.getSource && map.getSource("measure")) drawMeasure();
}
function drawMeasure() {
  const pts = state.measure || [], f = pts.map(p => ({ type: "Feature", properties: {}, geometry: { type: "Point", coordinates: p } }));
  let tot = 0, last = 0;
  // plan distance in the project's own coordinates (local metres, UTM grid), as on a drawing; else on the sphere
  const dist = (a, b) => {
    const p = projected({ lng: a[0], lat: a[1] }), q = projected({ lng: b[0], lat: b[1] });
    return p && p.e != null ? Math.hypot(q.e - p.e, q.n - p.n) : new maplibregl.LngLat(...a).distanceTo(new maplibregl.LngLat(...b));
  };
  for (let i = 1; i < pts.length; i++) { last = dist(pts[i - 1], pts[i]); tot += last; }
  if (pts.length > 1) f.push({ type: "Feature", properties: {}, geometry: { type: "LineString", coordinates: pts } });
  map.getSource("measure").setData({ type: "FeatureCollection", features: f });
  state.measureLength = tot;
  if (state.tool === "measure") $("#hint").textContent = pts.length > 1 ? `Length ${tot.toFixed(1)} m` + (pts.length > 2 ? ` over ${pts.length - 1} legs (last ${last.toFixed(1)} m)` : "") + `. Esc clears.` : HINTS.measure;
}
function wireView() {
  splitter($("#split-props"), "v"); splitter($("#split-bottom"), "h");
  $("#props-toggle").onclick = e => { e.stopPropagation(); setProps(!ui.propsCollapsed); };
  $("#props-head").onclick = () => { if (ui.propsCollapsed) setProps(false); };
  $("#bottom-toggle").onclick = () => setBottom(!ui.bottomCollapsed);
  $("#props-btn").onclick = () => setProps(!ui.propsCollapsed);
  $("#bottom-btn").onclick = () => setBottom(!ui.bottomCollapsed);
  $("#maxmap-btn").onclick = toggleMapOnly;
  $("#tools-compact-btn").onclick = () => { ui.toolsCompact = !ui.toolsCompact; applyPanels(); };
  $("#theme-btn").onclick = () => setTheme(ui.theme === "dark" ? "light" : "dark");
  $("#keys-btn").onclick = () => { $("#dlg-keys").hidden = false; }; $("#keys-close").onclick = () => { $("#dlg-keys").hidden = true; };
  $("#display-head").onclick = () => { ui.cardFolded = !ui.cardFolded; applyPanels(); };
  $("#basemap-select").onchange = e => { ui.basemap = e.target.value; saveUi(); applyBasemap(); };
  $("#basemap-opacity").oninput = e => { ui.opacity = +e.target.value; saveUi(); applyBasemap(); };
  $("#labels-toggle").onchange = e => { ui.labels = e.target.checked; saveUi(); applyBasemap(); };
  $("#hillshade-toggle").onchange = e => { ui.hillshade = e.target.checked; saveUi(); applyBasemap(); };
  $("#arrows-toggle").onchange = e => { ui.arrows = e.target.checked; saveUi(); applyBasemap(); };
  const setFail = on => { ui.showFail = on; saveUi(); applyBasemap(); renderLegend(); };
  $("#fail-toggle").onchange = e => setFail(e.target.checked);
  $("#legend").addEventListener("click", e => { if (e.target.closest(".fail-row")) setFail(!ui.showFail); });
  $("#find-input").addEventListener("keydown", e => { if (e.key === "Enter") { e.preventDefault(); findElement(e.target.value); } else if (e.key === "Escape") e.target.blur(); });
  $("#status-line").addEventListener("click", e => { const a = e.target.closest("a.fail"); if (a) { e.preventDefault(); stepFailure(a.dataset.flag); } });
  wireProfile();
  new ResizeObserver(redrawCharts).observe($("#panes"));
  addEventListener("resize", applyPanels);
  applyPanels(); document.body.classList.toggle("dark", ui.theme === "dark");
}

/* ------------------------------------------------------------------ batch 1: reload, cells and paste, trace, box select, reference layers */
/* ---- the open project comes back after a page reload (and, with the server's snapshots, after a restart) */
const SESS_KEY = "w19.session";
let sessT = 0;
function saveSession() {
  clearTimeout(sessT);
  sessT = setTimeout(() => {
    try {
      if (!state.pid) { localStorage.removeItem(SESS_KEY); return; }
      const c = map.getCenter();
      localStorage.setItem(SESS_KEY, JSON.stringify({ pid: state.pid, sid: state.sid, tab: state.tab, center: [c.lng, c.lat], zoom: map.getZoom() }));
    } catch (e) { /* private window: nothing kept */ }
  }, 300);
}
async function reattach() {
  let s = null; try { s = JSON.parse(localStorage.getItem(SESS_KEY) || "null"); } catch (e) { /* none */ }
  if (!s || !s.pid) return;
  let info; try { info = await jget(`/projects/${encodeURIComponent(s.pid)}`); } catch (e) { try { localStorage.removeItem(SESS_KEY); } catch (x) { /* */ } return; }
  await withBusy(`Reopening ${info.name}...`, async () => {
    await openProject(info, false);
    if (s.sid && s.sid !== "base" && info.scenarios.some(x => x.id === s.sid)) { state.sid = s.sid; await refreshAll(false); }
    if (s.center) map.jumpTo({ center: s.center, zoom: s.zoom });
    if (s.tab && s.tab !== state.tab) showTab(s.tab);
    toast(`Reopened ${info.name} where you left it.`, "info");
  });
}

/* ---- tables: double-click a cell to edit it; click a cell, then paste a column (or several) copied from Excel */
const EDITABLE = { nodes: ["kind", "ground", "invert", "inflow_m3d", "load"], links: ["kind", "length_m", "dn_mm", "up_inv", "dn_inv", "transfer"] };
function cellEditor(kind, td, id, col) {
  const f = tmap(kind).get(id); if (!f) return;
  const m = state.model, cur = col === "load" ? ((m.loads[m.settings.design_load] || {})[id] ?? 0) : f.properties[col];
  let html;
  if (col === "kind") html = `<select>${(kind === "nodes" ? state.info.node_kinds : state.info.link_kinds).map(o => `<option${o === cur ? " selected" : ""}>${o}</option>`).join("")}</select>`;
  else if (col === "dn_mm") html = `<select>${state.info.catalogue.map(o => `<option${o === cur ? " selected" : ""}>${o}</option>`).join("")}</select>`;
  else if (col === "transfer") html = `<select><option${cur ? " selected" : ""}>true</option><option${!cur ? " selected" : ""}>false</option></select>`;
  else html = `<input type="number" step="any" value="${typeof cur === "number" ? +cur.toFixed(4) : ""}">`;
  td.innerHTML = html; td.classList.add("editing");
  const inp = td.firstChild; inp.dataset.testid = "cell-editor"; inp.focus(); if (inp.select) inp.select();
  let done = false;
  const commit = next => {
    if (done) return; done = true;
    let v = inp.value;
    if (col === "transfer") v = v === "true"; else if (col !== "kind") { if (v === "") { renderTable(kind); return; } v = Number(v); if (!isFinite(v)) { renderTable(kind); return; } }
    const same = typeof cur === "number" && typeof v === "number" ? +cur.toFixed(4) === v : cur === v;
    const after = () => { if (next) { const vw = state.view[kind], i = vw.indexOf(id); if (i >= 0 && i + 1 < vw.length) openCell(kind, vw[i + 1], col); } };
    if (same) { renderTable(kind); after(); return; }
    enqueue(async () => {
      if (col === "load") await execMany([{ op: "set_loads", set: m.settings.design_load, values: { [id]: v } }]);
      else await setField(kind, [id], col, v);
      after();
    });
  };
  inp.addEventListener("keydown", e => {
    if (e.key === "Enter") { e.preventDefault(); commit(true); }
    else if (e.key === "Escape") { done = true; renderTable(kind); }
    else if (e.key === "Tab") { e.preventDefault(); commit(false); }
  });
  inp.addEventListener("blur", () => commit(false));
  if (inp.tagName === "SELECT") inp.addEventListener("change", () => commit(false));
}
function openCell(kind, id, col) {
  const st = state.table[kind], i = state.view[kind].indexOf(id); if (i < 0) return;
  const pg = Math.floor(i / PAGE); if (pg !== st.page) { st.page = pg; renderTable(kind); }
  const tr = $(`#tbl-${kind} tr[data-id="${CSS.escape(id)}"]`), ci = colsOf(kind).indexOf(col);
  if (tr && ci >= 0) { state.cell = { kind, id, col }; cellEditor(kind, tr.children[ci], id, col); }
}
function pasteCells(text) {
  const c = state.cell; if (!c || !state.model || state.tab !== c.kind) return false;
  const kind = c.kind, cols = colsOf(kind), c0 = cols.indexOf(c.col), view = state.view[kind], r0 = view.indexOf(c.id);
  if (c0 < 0 || r0 < 0) return false;
  const lines = text.replace(/\r/g, "").split("\n"); while (lines.length && !lines[lines.length - 1].trim()) lines.pop();
  if (!lines.length) return false;
  const grid = lines.map(l => l.split("\t")), ops = [], skipped = [];
  let n = 0;
  for (let j = 0; j < Math.max(...grid.map(r => r.length)); j++) {
    const col = cols[c0 + j];
    if (!col || !EDITABLE[kind].includes(col)) { if (col) skipped.push(col); continue; }
    const values = {};
    grid.forEach((row, i) => {
      const id = view[r0 + i]; if (id == null || row[j] == null || row[j].trim() === "") return;
      let v = row[j].trim();
      if (col === "transfer") v = /^(true|1|yes)$/i.test(v);
      else if (col !== "kind") { v = Number(v.replace(/,/g, "")); if (!isFinite(v)) return; }
      values[id] = v; n++;
    });
    if (!Object.keys(values).length) continue;
    ops.push(col === "load" ? { op: "set_loads", set: state.model.settings.design_load, values } : { op: "set_many", table: kind, field: col, values });
  }
  if (!ops.length) { toast(`Nothing to paste into ${c.col}: only ${EDITABLE[kind].join(", ")} can be edited here.`); return true; }
  enqueue(async () => {
    await execMany(ops);
    toast(`Pasted ${n} values into ${ops.map(o => o.field || "load").join(", ")} (${ops.length} undo step${ops.length > 1 ? "s" : ""})` + (skipped.length ? `; ${skipped.join(", ")} cannot be pasted into` : "") + ".", "info");
  });
  return true;
}

/* ---- trace upstream or downstream from a manhole or pipe: the pipes are selected and summed */
function traceFrom(table, id, dir) {
  const m = state.model; if (!m) return null;
  const into = new Map(), out = new Map();
  for (const f of m.linkFeat) {
    const p = f.properties;
    if (!into.has(p.to_node)) into.set(p.to_node, []); into.get(p.to_node).push(f);
    if (!out.has(p.from_node)) out.set(p.from_node, []); out.get(p.from_node).push(f);
  }
  const links = new Set(), nodes = new Set(), dist = new Map();
  let start = id;
  if (table === "links") { const f = m.links.get(id); if (!f) return null; links.add(id); start = dir === "up" ? f.properties.from_node : f.properties.to_node; }
  const q = [start]; nodes.add(start); dist.set(start, table === "links" ? (m.links.get(id).properties.length_m || 0) : 0);
  while (q.length) {
    const n = q.shift();
    for (const f of (dir === "up" ? into : out).get(n) || []) {
      if (links.has(String(f.id))) continue; links.add(String(f.id));
      const nx = dir === "up" ? f.properties.from_node : f.properties.to_node;
      if (!nodes.has(nx)) { nodes.add(nx); dist.set(nx, dist.get(n) + (f.properties.length_m || 0)); q.push(nx); }
    }
  }
  const R = srcLinks(), ls = m.loads[m.settings.design_load] || {};
  let km = 0, pumps = 0, fail = 0, vmin = null;
  for (const l of links) {
    const p = m.links.get(l).properties; km += (p.length_m || 0) / 1000; if (p.kind === "pump") pumps++;
    const r = R[l]; if (r && (r.over_limit || r.over_vmax || r.surcharged || r.negative_slope)) fail++;
    if (r && r.v_ms != null && p.kind !== "pump") vmin = vmin == null ? r.v_ms : Math.min(vmin, r.v_ms);
  }
  let far = start, fd = 0; for (const [n, d] of dist) if (d > fd) { fd = d; far = n; }
  const load = dir === "up" ? [...nodes].reduce((s, n) => s + (ls[n] || 0), 0) : null;
  const outLink = table === "links" ? id : ((out.get(id) || [])[0] || {}).id;
  return { dir, table, id, start, links: [...links], nodes: nodes.size, km, pumps, fail, vmin, far, farKm: fd / 1000, load,
           flow: outLink != null && R[outLink] ? R[outLink].q_ls : null, loadSet: m.settings.design_load };
}
function trace(dir) {
  if (!state.sel.ids.length || !["nodes", "links"].includes(state.sel.table)) { toast("Select a manhole or a pipe to trace from.", "info"); return; }
  const t = traceFrom(state.sel.table, state.sel.ids[0], dir); if (!t) return;
  if (!t.links.length) { toast(dir === "up" ? `Nothing drains to ${t.id}.` : `Nothing leaves ${t.id}.`, "info"); return; }
  state.trace = t; setSel("links", t.links, { zoom: true }); state.trace = t;
  renderProps();
}
function traceBox() {
  const t = state.trace;
  if (!t || state.sel.table !== "links" || state.sel.ids.length !== t.links.length || state.sel.ids[0] !== t.links[0]) return "";
  const up = t.dir === "up";
  return `<div class="trace-box" data-testid="trace-box"><b>${up ? "Upstream of" : "Downstream of"} ${esc(t.id)}</b><br>` +
    `${t.links.length - t.pumps} pipes${t.pumps ? ` + ${t.pumps} pumps` : ""} · ${num(t.km, 2)} km · ${t.nodes} nodes<br>` +
    (up ? `load ${num(t.load, 1)} m3/d (${esc(t.loadSet)})` + (t.flow != null ? ` · ${num(t.flow, 2)} L/s leaving` : "") + `<br>farthest: ${esc(t.far)} at ${num(t.farKm, 2)} km`
        : `ends at ${esc(t.far)} after ${num(t.farKm, 2)} km` + (t.vmin != null ? ` · lowest v ${num(t.vmin, 2)} m/s` : "")) +
    (t.fail ? `<br><span class="flag">${t.fail} failing</span>` : "") +
    `<div class="row"><button id="trace-profile">${up ? "Profile from the farthest" : "Profile to the end"}</button></div></div>`;
}
function traceProfile() {
  const t = state.trace; if (!t) return;
  $("#prof-start").value = t.dir === "up" ? t.far : t.id; $("#prof-end").value = t.dir === "up" ? (t.table === "links" ? t.id : t.id) : t.far; $("#prof-via").value = "";
  showTab("profile"); drawProfile();
}

/* ---- box select: Shift+drag selects the pipes whose middle is inside the box, Ctrl+drag the nodes */
let box = null;
function boxStart(e) {
  const o = e.originalEvent || {};
  if (state.tool !== "select" || !state.model || !(o.shiftKey || o.ctrlKey) || o.button !== 0) return;
  box = { a: e.point, b: e.point, nodes: o.ctrlKey && !o.shiftKey, el: null }; map.dragPan.disable();
}
function boxMove(e) {
  if (!box) return; box.b = e.point;
  if (!box.el) { box.el = document.createElement("div"); box.el.id = "selbox"; $("#map-wrap").appendChild(box.el); }
  const x = Math.min(box.a.x, box.b.x), y = Math.min(box.a.y, box.b.y);
  Object.assign(box.el.style, { left: x + "px", top: y + "px", width: Math.abs(box.b.x - box.a.x) + "px", height: Math.abs(box.b.y - box.a.y) + "px" });
}
function boxEnd(e) {
  if (!box) return; const b = box; box = null; map.dragPan.enable(); if (b.el) b.el.remove();
  const p = e.point, x0 = Math.min(b.a.x, p.x), x1 = Math.max(b.a.x, p.x), y0 = Math.min(b.a.y, p.y), y1 = Math.max(b.a.y, p.y);
  if (x1 - x0 < 4 && y1 - y0 < 4) return;                      // a click: the Select tool handles it
  suppressClick = true; setTimeout(() => { suppressClick = false; }, 80);
  const inside = c => { const q = map.project(c); return q.x >= x0 && q.x <= x1 && q.y >= y0 && q.y <= y1; };
  const m = state.model, ids = [];
  if (b.nodes) { for (const f of m.nodeFeat) if (inside(f.geometry.coordinates)) ids.push(String(f.id)); }
  else for (const f of m.linkFeat) {
    const c = f.geometry.coordinates, a0 = c[0], a1 = c[c.length - 1];
    if (inside([(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2])) ids.push(String(f.id));
  }
  setSel(b.nodes ? "nodes" : "links", ids);
  toast(`${ids.length} ${b.nodes ? "nodes" : "pipes"} selected. Edit them together in Properties or with Set field in the table.`, "info");
}

/* ---- reference layers: GIS files drawn under the network for orientation; display only, kept with the project */
const REF_COLORS = ["#d9480f", "#2b8a3e", "#5f3dc4", "#c2255c", "#1971c2", "#e67700", "#0b7285"];
function refLayerIds(r) { return ["fill", "line", "pt"].map(k => `ref-${r.id}-${k}`); }
function addRefToMap(r, i) {
  const col = r.color || REF_COLORS[i % REF_COLORS.length]; r.color = col; r.visible = r.visible !== false;
  const sid = "ref-" + r.id, before = map.getLayer("route-halo") ? "route-halo" : undefined;
  if (!map.getSource(sid)) map.addSource(sid, { type: "geojson", data: r.geojson, tolerance: 0.4 });
  const vis = r.visible ? "visible" : "none", gt = ["geometry-type"];
  map.addLayer({ id: `ref-${r.id}-fill`, type: "fill", source: sid, filter: ["==", gt, "Polygon"], layout: { visibility: vis }, paint: { "fill-color": col, "fill-opacity": 0.12, "fill-outline-color": col } }, before);
  map.addLayer({ id: `ref-${r.id}-line`, type: "line", source: sid, filter: ["in", gt, ["literal", ["LineString", "Polygon"]]], layout: { visibility: vis }, paint: { "line-color": col, "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.6, 17, 1.6], "line-opacity": 0.8 } }, before);
  map.addLayer({ id: `ref-${r.id}-pt`, type: "circle", source: sid, filter: ["==", gt, "Point"], layout: { visibility: vis }, paint: { "circle-radius": 3, "circle-color": col, "circle-stroke-color": "#fff", "circle-stroke-width": 1 } }, before);
}
function removeRefFromMap(r) {
  for (const l of refLayerIds(r)) if (map.getLayer(l)) map.removeLayer(l);
  if (map.getSource("ref-" + r.id)) map.removeSource("ref-" + r.id);
}
async function loadRefs() {
  await mapReady;
  for (const r of state.refs || []) removeRefFromMap(r);
  state.refs = [];
  if (!state.pid) { renderRefs(); return; }
  try { state.refs = await jget(`/projects/${state.pid}/reference`); } catch (e) { state.refs = []; }
  state.refs.forEach(addRefToMap); renderRefs();
}
function renderRefs() {
  const host = $("#ref-list"); if (!host) return;
  host.innerHTML = (state.refs || []).map(r => `<div class="ref" data-rid="${esc(r.id)}"><span class="sw" style="background:${r.color}"></span>` +
    `<label title="${esc(r.count + " features" + (r.crs ? ", EPSG:" + r.crs : ", in the project's coordinates"))}"><input type="checkbox" data-act="vis" ${r.visible ? "checked" : ""}> ${esc(r.name)}</label>` +
    `<button class="pbtn" data-act="zoom" title="Zoom to the layer">&#9635;</button><button class="pbtn" data-act="del" title="Remove the layer">&times;</button></div>`).join("") ||
    `<div class="muted">None. Plots, roads, a survey DXF: drawn under the network.</div>`;
  tag(host);
}
async function addRefFile(file) {
  if (!state.pid || !file) return;
  const fd = new FormData(); fd.append("file", file);
  const r = await (await api(`/projects/${state.pid}/reference`, { method: "POST", body: fd })).json();
  await mapReady; state.refs = (state.refs || []).concat([r]); addRefToMap(r, state.refs.length - 1); renderRefs();
  toast(`${r.name}: ${r.count} features drawn under the network.`, "info");
}
function refFeatureTip(point) {
  const ids = (state.refs || []).filter(r => r.visible).flatMap(refLayerIds).filter(l => map.getLayer(l)); if (!ids.length) return "";
  const f = map.queryRenderedFeatures([[point.x - 3, point.y - 3], [point.x + 3, point.y + 3]], { layers: ids })[0]; if (!f) return "";
  const r = state.refs.find(x => f.layer.id.startsWith(`ref-${x.id}-`)), kv = Object.entries(f.properties).filter(([, v]) => v !== "" && v != null && v !== "None" && v !== "nan").slice(0, 4);
  return `<b>${esc(r ? r.name : "layer")}</b>` + kv.map(([k, v]) => ` · ${esc(k)}: ${esc(typeof v === "number" ? +v.toFixed(3) : String(v).slice(0, 40))}`).join("");
}
function wireBatch1() {
  map.on("mousedown", boxStart);
  map.on("mousemove", e => { if (box) boxMove(e); });
  map.on("mouseup", boxEnd);
  map.on("moveend", saveSession);
  for (const kind of ["nodes", "links"]) {
    const tbl = $("#tbl-" + kind);
    // the row click re-draws the table, so the browser's dblclick never fires on the cell: a second click on the same
    // cell within 450 ms is the double-click
    let last = { key: "", t: 0 };
    tbl.addEventListener("click", e => {
      const td = e.target.closest("td"), tr = e.target.closest("tr[data-id]"); if (!td || !tr || td.classList.contains("editing")) return;
      const id = tr.dataset.id, col = colsOf(kind)[td.cellIndex], key = `${id}|${col}`, now = performance.now();
      state.cell = { kind, id, col };
      const live = $(`#tbl-${kind} tr[data-id="${CSS.escape(id)}"]`);
      $$(`#tbl-${kind} td.cur`).forEach(x => x.classList.remove("cur")); if (live) live.children[td.cellIndex].classList.add("cur");
      if (last.key === key && now - last.t < 450) {
        last = { key: "", t: 0 };
        if (!EDITABLE[kind].includes(col)) { toast(`${col} is not edited here (${EDITABLE[kind].join(", ")} are).`, "info"); return; }
        openCell(kind, id, col); return;
      }
      last = { key, t: now };
    });
  }
  document.addEventListener("paste", e => {
    const tg = e.target.tagName; if (["INPUT", "SELECT", "TEXTAREA"].includes(tg)) return;
    const t = (e.clipboardData || window.clipboardData).getData("text"); if (t && pasteCells(t)) e.preventDefault();
  });
  $("#ref-add").onclick = () => { if (!state.pid) { toast("Open a project first.", "info"); return; } $("#ref-file").click(); };
  $("#ref-file").onchange = e => { const f = e.target.files[0]; e.target.value = ""; if (f) enqueue(() => withBusy(`Reading ${f.name}...`, () => addRefFile(f))); };
  $("#ref-list").addEventListener("click", e => {
    const row = e.target.closest(".ref"); if (!row) return; const r = state.refs.find(x => x.id === row.dataset.rid); if (!r) return;
    const act = e.target.dataset.act;
    if (act === "vis") { r.visible = e.target.checked; for (const l of refLayerIds(r)) if (map.getLayer(l)) map.setLayoutProperty(l, "visibility", r.visible ? "visible" : "none"); }
    else if (act === "zoom") { const pts = []; const walk = c => typeof c[0] === "number" ? pts.push(c) : c.forEach(walk); r.geojson.features.forEach(f => walk(f.geometry.coordinates)); if (pts.length) { const b = bboxOf(pts); map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 40, maxZoom: 18, duration: 300 }); } }
    else if (act === "del") enqueue(async () => { await jpost(`/projects/${state.pid}/reference/${encodeURIComponent(r.id)}/delete`); removeRefFromMap(r); state.refs = state.refs.filter(x => x !== r); renderRefs(); });
  });
  $("#props").addEventListener("click", e => {
    if (e.target.id === "trace-up") trace("up"); else if (e.target.id === "trace-down") trace("down"); else if (e.target.id === "trace-profile") traceProfile();
  });
  renderRefs();
}

/* ------------------------------------------------------------------ batch 2: scenarios, summary, storm slider, design control, quantities, assistant on the map */
/* ---- a small modal for a name or a yes/no */
function askText(title, label, value, confirmOnly) {
  return new Promise(res => {
    const d = $("#dlg-ask"), i = $("#ask-input");
    $("#ask-title").textContent = title; $("#ask-label").textContent = label || ""; i.value = value || "";
    i.style.display = confirmOnly ? "none" : ""; $("#ask-ok").textContent = confirmOnly ? "Yes" : "OK"; d.hidden = false;
    setTimeout(() => (confirmOnly ? $("#ask-ok") : i).focus(), 0); if (!confirmOnly) i.select();
    const done = v => { d.hidden = true; $("#ask-ok").onclick = $("#ask-cancel").onclick = null; d.onkeydown = null; res(v); };
    $("#ask-ok").onclick = () => done(confirmOnly ? true : (i.value.trim() || null));
    $("#ask-cancel").onclick = () => done(null);
    d.onkeydown = e => { if (e.key === "Enter") { e.preventDefault(); $("#ask-ok").click(); } else if (e.key === "Escape") done(null); };
  });
}

/* ---- scenario manager: the scenarios as a tree; open, copy, rename, delete (with their copies), compare */
function scenTree() {
  const sc = state.info.scenarios, out = [];
  const walk = (parent, d) => { for (const s of sc.filter(x => (x.parent || null) === parent)) { out.push([s, d]); walk(s.id, d + 1); } };
  walk(null, 0); return out;
}
function openScenDlg() { if (!state.pid) return; renderScenDlg(); $("#dlg-scen").hidden = false; }
function renderScenDlg() {
  $("#scen-list").innerHTML = scenTree().map(([s, d]) => `<div class="scrow${s.id === state.sid ? " cur" : ""}" data-sid="${esc(s.id)}">` +
    `<span class="scname" style="padding-left:${d * 16}px">${d ? "└ " : ""}${esc(s.name)}</span><span class="muted">${s.edits} edits</span>` +
    `<button data-a="open" ${s.id === state.sid ? "disabled" : ""}>Open</button><button data-a="copy">Copy</button><button data-a="rename">Rename</button>` +
    `<button data-a="compare" ${s.id === state.sid ? "disabled" : ""} title="Colour the open scenario by what changed against this one">Compare</button>` +
    `<button data-a="del" ${s.id === "base" ? "disabled" : ""}>Delete</button></div>`).join("");
  tag($("#scen-list"));
}
async function switchScenario(sid) {
  state.sid = sid; state.sel = { table: null, ids: [] }; $("#settings-form").dataset.sig = "";
  if (state.compare && state.compare.b !== sid) clearCompare();
  stopStormPlay(); state.stormFrame = null;
  await refreshAll(false); saveSession();
}
async function scenAction(a, sid) {
  // the questions are asked here, outside the edit queue (an open prompt must not hold up other work); the server calls queue
  const s = state.info.scenarios.find(x => x.id === sid); if (!s) return;
  const after = () => { if (!$("#dlg-scen").hidden) renderScenDlg(); };
  if (a === "open") return enqueue(async () => { await switchScenario(sid); after(); });
  if (a === "compare") return enqueue(async () => { await compareWith(sid); $("#dlg-scen").hidden = true; });
  if (a === "copy") {
    const name = await askText("Copy scenario", "Name of the copy", `${s.name} copy`); if (!name) return;
    return enqueue(async () => { const r = await jpost(`/projects/${state.pid}/scenarios/${encodeURIComponent(sid)}/copy`, { name }); state.info = r; await switchScenario(r.created); after(); });
  }
  if (a === "rename") {
    const name = await askText("Rename scenario", "New name", s.name); if (!name) return;
    return enqueue(async () => { state.info = await jpost(`/projects/${state.pid}/scenarios/${encodeURIComponent(sid)}/rename`, { name }); updateButtons(); after(); });
  }
  if (a === "del") {
    const kids = scenTree().filter(([x]) => { let p = x; while (p && p.parent) { if (p.parent === sid) return true; p = state.info.scenarios.find(y => y.id === p.parent); } return false; }).length;
    if (!await askText("Delete scenario", `Delete "${s.name}"${kids ? ` and the ${kids} scenario${kids > 1 ? "s" : ""} copied from it` : ""}? Undo cannot bring it back.`, "", true)) return;
    return enqueue(async () => {
      const r = await jpost(`/projects/${state.pid}/scenarios/${encodeURIComponent(sid)}/delete`); state.info = r;
      if (!r.scenarios.some(x => x.id === state.sid)) await switchScenario("base"); else updateButtons();
      after();
    });
  }
}
/* ---- compare: the open scenario coloured by what changed against another; the differences in Tool output */
const CHANGE_COL = { size: "#8e44ad", levels: "#e67e22", flow: "#2e86de", added: "#27ae60", same: "#c3cad3" };
async function compareWith(a) {
  const r = await jget(`/projects/${state.pid}/compare?a=${encodeURIComponent(a)}&b=${encodeURIComponent(state.sid)}`);
  const an = state.info.scenarios.find(x => x.id === a).name;
  state.compare = { ...r, aName: an };
  state.colorBy = "compare"; $("#color-by").value = "compare";
  state.toolout = { tool: { name: "compare", label: `Compared with ${an}: what changed in the open scenario` }, rows: r.rows.map(x => ({ ...x, change: r.change[x.id] })),
                    cols: ["id", "change", "dn_mm_a", "dn_mm_b", "up_inv_a", "up_inv_b", "dn_inv_a", "dn_inv_b", "q_ls_a", "q_ls_b", "v_ms_a", "v_ms_b", "dv"], report: { ...r.counts } };
  mergeResults(); showTab("toolout"); renderAll();
}
function clearCompare() {
  const was = state.colorBy === "compare"; state.compare = null;
  if (was) { state.colorBy = "v_ms"; $("#color-by").value = "v_ms"; if (state.model) { mergeResults(); pushMap(); } renderLegend(); }
}

/* ---- the summary: the network at a glance, from the solved results; every bar selects its pipes */
function barChart(id, title, unit, bars, onClick) {
  const W = 360, rowH = 17, H = 26 + bars.length * rowH + 6, mx = Math.max(1e-9, ...bars.map(b => b.value));
  let s = `<svg id="${id}" class="bars" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}"><text x="0" y="13" class="bt">${esc(title)}</text>`;
  bars.forEach((b, k) => {
    const y = 24 + k * rowH, w = Math.max(b.value > 0 ? 1.5 : 0, (W - 150) * b.value / mx);
    s += `<g class="bar" data-k="${k}"><title>${esc(b.label)}: ${num(b.value, 2)} ${unit}${b.n != null ? ` (${b.n})` : ""}</title><text x="78" y="${y + 11}" text-anchor="end">${esc(b.label)}</text>` +
      `<rect x="84" y="${y + 2}" width="${w}" height="${rowH - 5}" rx="2" fill="${b.color || "#4c78b8"}"/><text x="${88 + w}" y="${y + 11}">${num(b.value, b.value >= 100 ? 0 : 2)}</text></g>`;
  });
  s += `</svg>`;
  return { html: s, wire: () => $$(`#${id} .bar`).forEach(g => g.addEventListener("click", () => onClick && onClick(bars[+g.dataset.k]))) };
}
function renderSummary() {
  const host = $("#summary"); if (!host) return;
  const m = state.model, R = srcLinks(), s = state.summary;
  if (!m || !s) { host.innerHTML = `<p class="muted">Open a project.</p>`; return; }
  const L = m.linkFeat.filter(f => f.properties.kind !== "pump"), km = f => (f.properties.length_m || 0) / 1000;
  const sel = ids => { setSel("links", ids, { zoom: true }); toast(`${ids.length} pipes selected.`, "info"); };
  const kpi = (lab, val, flag) => `<div class="kpi${flag ? " bad" : ""}"${flag ? ` data-flag="${flag}" title="Click to step through them"` : ""}><div class="kv">${val}</div><div class="kl">${lab}</div></div>`;
  let h = `<div class="kpis">` + kpi("pipes", L.length) + kpi("km", num(s.km, 2)) +
    kpi("over the d/D limit", s.over_limit ?? 0, s.over_limit ? "over_limit" : null) + kpi("over v max", s.over_vmax ?? 0, s.over_vmax ? "over_vmax" : null) +
    kpi("surcharged", s.surcharged ?? 0, s.surcharged ? "surcharged" : null) + kpi("flat or adverse", s.negative_slope ?? 0, s.negative_slope ? "negative_slope" : null) +
    (s.km_under_vmin != null ? kpi(`km under v min (${esc(s.check_set)})`, num(s.km_under_vmin, 2)) : "") + `</div><div class="charts">`;
  // km by size
  const byDn = new Map(); for (const f of L) { const d = f.properties.dn_mm; const e = byDn.get(d) || { value: 0, ids: [] }; e.value += km(f); e.ids.push(String(f.id)); byDn.set(d, e); }
  const c1 = barChart("ch-dn", "Length by size (km)", "km", [...byDn.entries()].sort((a, b) => a[0] - b[0]).map(([d, e]) => ({ label: `DN${d}`, value: e.value, n: e.ids.length, ids: e.ids, color: colourFor("dn_mm", d) })), b => sel(b.ids));
  const binned = (by, sc) => sc.bins.map((bin, k) => {
    const lo = k ? sc.bins[k - 1][0] : -Infinity, fs = L.filter(f => { const r = R[f.id]; return r && r[by] != null && r[by] > lo && r[by] <= bin[0]; });
    return { label: bin[1], value: fs.reduce((a, f) => a + km(f), 0), n: fs.length, ids: fs.map(f => String(f.id)), color: bin[2] };
  });
  const c2 = barChart("ch-v", "Velocity (km of pipe)", "km", binned("v_ms", SCALES.v_ms), b => sel(b.ids));
  const c3 = barChart("ch-dd", "d/D (km of pipe)", "km", binned("d_over_D", SCALES.d_over_D), b => sel(b.ids));
  h += c1.html + c2.html + c3.html + `</div>`;
  host.innerHTML = h; c1.wire(); c2.wire(); c3.wire();
  $$("#summary .kpi[data-flag]").forEach(k => k.addEventListener("click", () => stepFailure(k.dataset.flag)));
}

/* ---- storm time slider: colour the map at any reporting period of the last storm run, or play it */
let stormTimer = null, frameSeq = 0;
function stormBar() {
  const bar = $("#storm-bar"), S = stormNow(), show = !!S && ["storm_cap", "storm_q", "storm_flood"].includes(state.colorBy);
  bar.hidden = !show; if (!show) { stopStormPlay(); return; }
  const n = S.summary.periods, t = $("#storm-t"); t.max = Math.max(0, n - 1);
  if (!state.stormFrame) t.value = t.max;
  const f = state.stormFrame, step = S.summary.report_step_s || 60;
  const hhmm = s => `${String(Math.floor(s / 3600)).padStart(2, "0")}:${String(Math.floor(s % 3600 / 60)).padStart(2, "0")}`;
  $("#storm-time").textContent = f ? `t = ${hhmm(f.t_s)}` : `peaks over ${hhmm(n * step)}`;
  $("#storm-peak").disabled = !f;
}
async function loadFrame(k) {
  const S = stormNow(); if (!S) return;
  const attr = state.colorBy === "storm_q" ? "flow_rate" : "capacity", seq = ++frameSeq;
  const f = await jget(`${base()}/storm/frame?period=${k}&attr=${attr}`);
  if (seq !== frameSeq) return;
  state.stormFrame = { ...f, sid: state.sid }; mergeResults(); pushMap(); renderLegend(); stormBar();
}
function stopStormPlay() { if (stormTimer) { clearInterval(stormTimer); stormTimer = null; } const b = $("#storm-play"); if (b) b.textContent = "▶"; }
function toggleStormPlay() {
  if (stormTimer) { stopStormPlay(); return; }
  const t = $("#storm-t"); if (+t.value >= +t.max) t.value = 0;
  $("#storm-play").textContent = "❚❚";
  stormTimer = setInterval(() => { const k = +t.value + 1; if (k > +t.max) { stopStormPlay(); return; } t.value = k; loadFrame(k); }, 260);
}

/* ---- design: the whole network or the selected pipes, previewed before it is applied; locked pipes kept */
function openDesignDlg() {
  if (!state.pid) return;
  const nsel = state.sel.table === "links" ? state.sel.ids.length : 0, locked = lockedSet().size;
  $("#des-sel-n").textContent = nsel ? `${nsel} selected pipe${nsel > 1 ? "s" : ""}` : "(select pipes first)";
  $("#des-scope-sel").disabled = !nsel; if (!nsel) $("#des-scope-all").checked = true;
  $("#des-locked").textContent = locked ? `${locked} locked pipe${locked > 1 ? "s" : ""} keep their size and levels.` : "No pipe is locked.";
  $("#des-load").innerHTML = Object.keys(state.model.loads || {}).map(k => `<option${k === state.model.settings.design_load ? " selected" : ""}>${esc(k)}</option>`).join("");
  $("#dlg-design").hidden = false;
}
function designOpts() {
  const only = $("#des-scope-sel").checked && state.sel.table === "links" ? state.sel.ids.slice() : null;
  return { only, load: $("#des-load").value };
}
async function runDesign(preview, o) {
  o = o || designOpts();
  const r = await jpost(`${base()}/design?load_set=${encodeURIComponent(o.load)}`, { only: o.only, preview });
  if (preview) {
    state.toolout = { tool: { name: "design_preview", label: `Design preview${o.only ? ` (${o.only.length} selected pipes)` : ""}: nothing is changed until you apply it` },
                      rows: r.rows, cols: ["id", "dn_old", "dn_new", "up_old", "up_new", "dn_inv_old", "dn_inv_new", "d_up"],
                      report: { links_changed: r.links_changed, sizes_changed: r.sizes_changed, nodes_moved: r.nodes_moved, ...r.report }, apply: o };
  } else {
    state.toolout = { tool: { name: "design", label: `Design${o.only ? ` of ${o.only.length} selected pipes` : ""}: sizes and levels (undo takes it back)` }, rows: [], report: r.report };
    if (r.scenario) updateScenario(r.scenario); state.summary = r.summary; await loadModel(); await loadResults();
  }
  showTab("toolout"); renderAll();
}
const lockedSet = () => new Set(((state.model && state.model.settings.design) || {}).locked || []);
async function setLock(ids, locked) { await execMany([{ op: "lock", ids, locked }]); toast(`${ids.length} pipe${ids.length > 1 ? "s" : ""} ${locked ? `locked: the design keeps ${ids.length > 1 ? "their sizes" : "its size"} and levels` : "unlocked"}.`, "info"); }

/* ---- saved routes of the profile, kept with the project */
async function loadRoutes() {
  state.routes = state.pid ? await jget(`/projects/${state.pid}/routes`).catch(() => []) : []; renderRoutes();
}
function renderRoutes() {
  const s = $("#prof-routes"); if (!s) return;
  s.innerHTML = `<option value="">Saved routes (${(state.routes || []).length})</option>` + (state.routes || []).map(r => `<option value="${esc(r.name)}">${esc(r.name)}</option>`).join("");
  $("#prof-del-route").disabled = true;
}

/* ---- the CSV of whatever is in Tool output */
function toolCsv() {
  const o = state.toolout; if (!o || !o.rows.length) return;
  const cols = o.cols || Object.keys(o.rows[0]);
  const cell = v => v == null ? "" : /[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : v;
  downloadBlob(new Blob([[cols.join(",")].concat(o.rows.map(r => cols.map(c => cell(r[c])).join(","))).join("\n")], { type: "text/csv" }), `${o.tool.name || "tool"}.csv`);
}

function wireBatch2() {
  $("#scen-btn").onclick = openScenDlg; $("#scen-close").onclick = () => { $("#dlg-scen").hidden = true; };
  $("#scen-list").addEventListener("click", e => { const b = e.target.closest("button[data-a]"); if (!b) return; scenAction(b.dataset.a, b.closest(".scrow").dataset.sid); });
  $("#storm-t").addEventListener("input", e => { stopStormPlay(); enqueue(() => loadFrame(+e.target.value)); });
  $("#storm-play").onclick = toggleStormPlay;
  $("#storm-peak").onclick = () => { stopStormPlay(); state.stormFrame = null; mergeResults(); pushMap(); renderLegend(); stormBar(); };
  $("#des-preview").onclick = () => { $("#dlg-design").hidden = true; enqueue(() => withBusy("Design preview...", () => runDesign(true))); };
  $("#des-run").onclick = () => { $("#dlg-design").hidden = true; enqueue(() => withBusy("Design...", () => runDesign(false))); };
  $("#des-cancel").onclick = () => { $("#dlg-design").hidden = true; };
  $("#toolout-apply").onclick = () => { const o = state.toolout && state.toolout.apply; if (o) enqueue(() => withBusy("Design...", () => runDesign(false, o))); };
  $("#toolout-csv").onclick = toolCsv;
  $("#export-kmz-btn").onclick = () => enqueue(async () => { if (state.pid) saveBlob(await api(`/projects/${state.pid}/export.kmz?sid=${encodeURIComponent(state.sid)}`), "network.kmz"); });
  $("#prof-routes").onchange = e => {
    const r = (state.routes || []).find(x => x.name === e.target.value); $("#prof-del-route").disabled = !r; if (!r) return;
    $("#prof-start").value = r.start; $("#prof-end").value = r.end || ""; $("#prof-via").value = r.via || ""; drawProfile();
  };
  $("#prof-save-route").onclick = async () => {
    const start = $("#prof-start").value.trim(); if (!start) { toast("Draw a route first.", "info"); return; }
    const name = await askText("Save route", "Name of the route", `${start} to ${$("#prof-end").value.trim() || "outfall"}`); if (!name) return;
    const body = { name, start, end: $("#prof-end").value.trim(), via: $("#prof-via").value.trim() };
    enqueue(async () => { state.routes = await jpost(`/projects/${state.pid}/routes`, body); renderRoutes(); $("#prof-routes").value = name; $("#prof-del-route").disabled = false; });
  };
  $("#prof-del-route").onclick = () => enqueue(async () => {
    const name = $("#prof-routes").value; if (!name) return;
    state.routes = await jpost(`/projects/${state.pid}/routes/delete`, { name }); renderRoutes();
  });
  $("#props").addEventListener("click", e => {
    if (e.target.id === "lock-on" || e.target.id === "lock-off") { const ids = state.sel.ids.slice(); enqueue(() => setLock(ids, e.target.id === "lock-on")); }
  });
}

/* ------------------------------------------------------------------ boot */
state.history = [];
initMap(); wireUi(); initTables(); wireBatch1(); wireBatch2(); tag(); renderLegend(); updateStatus(); updateButtons(); asstStatus();
enqueue(reattach);
window.ed = {
  state, map,
  clickAt: (lon, lat, mods) => enqueue(() => act({ lng: lon, lat: lat }, mods)),
  selectElement: (table, id) => { setSel(table, [String(id)], { zoom: false }); return chain; },
  counts: () => state.model ? { nodes: state.model.nodeFeat.length, links: state.model.linkFeat.length } : { nodes: 0, links: 0 },
  idle: () => chain,
  finish: () => { finishCatchment(); return chain; },
};
