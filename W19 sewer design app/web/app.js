"use strict";
/* Sewer design app: browser interface. Plain JS, MapLibre GL, no build step. */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => Array.from(r.querySelectorAll(s));
const DN_CATALOGUE = [200, 250, 280, 315, 355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1100, 1200, 1400, 1600, 1800, 2000];
const fmt = (n, d = 0) => (n == null || Number.isNaN(n)) ? "–" : Number(n).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

const state = {
  scenarios: [], sid: null, case: null, results: null, summary: null, selected: [], props: null,
  pipeFeatures: 0, pushedCase: null, ready: false, lastSeconds: null, colorBy: "dn_mm", geoCase: null,
  tools: [], assistant: { available: false }, history: [], rows: [], sort: { col: "i", dir: 1 }, shown: 200,
};
const geoCache = {};
let map, mapLoaded, geo = null;

/* ------------------------------------------------------------------ api */
async function api(path, opts) {
  const r = await fetch(path, opts);
  if (!r.ok) { let t = ""; try { t = await r.text(); } catch (e) {} throw new Error(`${r.status} ${t.slice(0, 300)}`); }
  return r.json();
}
const post = (p, b) => api(p, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(b || {}) });
function toast(msg) {
  const t = $("#toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(toast._t); toast._t = setTimeout(() => { t.hidden = true; }, 5000);
}
function busy(on, text) { $("#busy").hidden = !on; if (text) $("#busy-text").textContent = text; }
const current = () => state.scenarios.find(s => s.id === state.sid);
const readOnly = () => { const s = current(); return !s || s.read_only; };

/* ------------------------------------------------------------------ colours */
const C_GREY = "#9aa5b1";
const SCALES = {
  dn_mm: { title: "Size DN (mm)", bins: [[250, "≤ 250", "#9ecae1"], [315, "280–315", "#6baed6"], [400, "355–400", "#4292c6"], [500, "450–500", "#2171b5"], [630, "560–630", "#6a51a3"], [800, "710–800", "#8c2d8c"], [1000, "900–1000", "#b0307a"], [1e9, "> 1000", "#7a0e3a"]] },
  v_ms: { title: "Velocity (m/s)", bins: [[0.75, "< 0.75", "#2166ac"], [1.5, "0.75–1.5", "#66bd63"], [2.5, "1.5–2.5", "#fdae61"], [3.0, "2.5–3.0", "#f46d43"], [1e9, "> 3.0", "#a50026"]] },
  d_over_D: { title: "d/D", bins: [[0.3, "< 0.30", "#c6dbef"], [0.5, "0.30–0.50", "#6baed6"], [0.7, "0.50–0.70", "#fdae61"], [0.8, "0.70–0.80", "#f46d43"], [1e9, "> 0.80", "#a50026"]] },
};
SCALES.v2031_ms = { ...SCALES.v_ms, title: "Velocity at 2031 (m/s)" };
function colourOf(by, cols, k) {
  if (by === "needs_relay") return cols.needs_relay[k] ? "#e6821e" : C_GREY;
  if (by === "failing") return (cols.over_limit[k] || cols.over_3ms[k]) ? "#d7301f" : C_GREY;
  const v = cols[by][k], bins = SCALES[by].bins;
  if (v == null) return C_GREY;
  for (const b of bins) if (v <= b[0]) return b[2];
  return bins[bins.length - 1][2];
}
function widthOf(dn) { return dn <= 250 ? 1 : dn <= 400 ? 1.5 : dn <= 630 ? 2.2 : dn <= 1000 ? 3 : 4; }
function renderLegend() {
  const by = state.colorBy, el = $("#legend");
  let rows;
  if (by === "needs_relay") rows = [["#e6821e", "needs re-lay (dashed)"], [C_GREY, "as laid"]];
  else if (by === "failing") rows = [["#d7301f", "over limit or over 3 m/s"], [C_GREY, "passing"]];
  else rows = SCALES[by].bins.map(b => [b[2], b[1]]);
  const title = by === "needs_relay" ? "Needs re-lay" : by === "failing" ? "Failing" : SCALES[by].title;
  el.innerHTML = `<div class="t">${title}</div>` + rows.map(r => `<div class="r"><span class="sw" style="background:${r[0]}"></span>${esc(r[1])}</div>`).join("") +
    `<div class="r"><span class="sw" style="background:#d7301f;outline:1px solid #fff"></span>red on top = failing</div>`;
}

/* ------------------------------------------------------------------ map */
function initMap() {
  map = new maplibregl.Map({
    container: "map", center: [56.5, 23.2], zoom: 11, boxZoom: false, attributionControl: true,
    style: {
      version: 8, glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
      sources: { osm: { type: "raster", tiles: ["https://tile.openstreetmap.org/{z}/{x}/{y}.png"], tileSize: 256, attribution: "© OpenStreetMap contributors", maxzoom: 19 } },
      layers: [{ id: "osm", type: "raster", source: "osm" }],
    },
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  map.addControl(new maplibregl.ScaleControl({ unit: "metric" }), "bottom-right");
  mapLoaded = new Promise(res => map.on("load", res));
  mapLoaded.then(() => {
    map.addSource("pipes", { type: "geojson", data: { type: "FeatureCollection", features: [] }, tolerance: 0.6 });
    map.addSource("nodes", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    map.addSource("sel", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
    const wExpr = k => ["interpolate", ["exponential", 1.6], ["zoom"], 10, ["*", ["get", "w"], 0.35 * k], 17, ["*", ["get", "w"], 2.6 * k]];
    map.addLayer({ id: "pipes-base", type: "line", source: "pipes", layout: { "line-cap": "round" }, paint: { "line-color": ["get", "c"], "line-width": wExpr(1) } });
    map.addLayer({ id: "pipes-fail", type: "line", source: "pipes", filter: ["==", ["get", "fail"], 1], paint: { "line-color": "#d7301f", "line-width": wExpr(1.3) } });
    map.addLayer({ id: "pipes-relay", type: "line", source: "pipes", filter: ["==", ["get", "relay"], 1], paint: { "line-color": "#e6821e", "line-width": wExpr(1.1), "line-dasharray": [2, 1.5] } });
    map.addLayer({ id: "pipes-sel-casing", type: "line", source: "sel", paint: { "line-color": "#ffffff", "line-width": 9 } });
    map.addLayer({ id: "pipes-sel", type: "line", source: "sel", paint: { "line-color": "#00b3c7", "line-width": 5 } });
    map.addLayer({ id: "nodes-mh", type: "circle", source: "nodes", minzoom: 14.5, filter: ["==", ["get", "kind"], "manhole"], paint: { "circle-radius": 2.2, "circle-color": "#fff", "circle-stroke-color": "#333", "circle-stroke-width": 0.8 } });
    map.addLayer({ id: "nodes-st", type: "circle", source: "nodes", filter: ["!=", ["get", "kind"], "manhole"], paint: { "circle-radius": ["interpolate", ["linear"], ["zoom"], 10, 4, 16, 8], "circle-color": ["match", ["get", "kind"], "pump", "#8e24aa", "lift", "#1b9e77", "plant inlet", "#111", "#555"], "circle-stroke-color": "#fff", "circle-stroke-width": 1.5 } });
    map.addLayer({ id: "nodes-st-label", type: "symbol", source: "nodes", filter: ["!=", ["get", "kind"], "manhole"], layout: { "text-field": ["get", "label"], "text-size": 11, "text-offset": [0, 1.2], "text-anchor": "top", "text-font": ["Open Sans Regular"] }, paint: { "text-color": "#222", "text-halo-color": "#fff", "text-halo-width": 1.5 } });
    map.on("click", "pipes-base", e => {
      if (e.originalEvent.shiftKey) return;
      const f = e.features && e.features[0]; if (f) selectPipe(f.properties.i);
    });
    map.on("mousemove", e => { map.getCanvas().style.cursor = map.queryRenderedFeatures(pad(e.point, 3), { layers: ["pipes-base"] }).length ? "pointer" : ""; });
    setupBoxSelect();
  });
  $("#basemap-toggle").addEventListener("change", e => {
    mapLoaded.then(() => map.setLayoutProperty("osm", "visibility", e.target.checked ? "visible" : "none"));
  });
}
const pad = (p, r) => [[p.x - r, p.y - r], [p.x + r, p.y + r]];

function setupBoxSelect() {
  const cont = map.getCanvasContainer(); let start = null, box = null;
  cont.addEventListener("mousedown", e => {
    if (!e.shiftKey || e.button !== 0) return;
    e.stopPropagation(); e.preventDefault();
    const r = cont.getBoundingClientRect(); start = { x: e.clientX - r.left, y: e.clientY - r.top };
    box = document.createElement("div"); box.className = "boxsel"; cont.appendChild(box);
    const move = ev => {
      const x = ev.clientX - r.left, y = ev.clientY - r.top;
      Object.assign(box.style, { left: Math.min(x, start.x) + "px", top: Math.min(y, start.y) + "px", width: Math.abs(x - start.x) + "px", height: Math.abs(y - start.y) + "px" });
    };
    const up = ev => {
      window.removeEventListener("mousemove", move); window.removeEventListener("mouseup", up, true);
      const x = ev.clientX - r.left, y = ev.clientY - r.top; box.remove(); box = null;
      const small = Math.abs(x - start.x) < 4 && Math.abs(y - start.y) < 4;
      const bb = small ? pad({ x, y }, 4) : [[Math.min(x, start.x), Math.min(y, start.y)], [Math.max(x, start.x), Math.max(y, start.y)]];
      const ids = [...new Set(map.queryRenderedFeatures(bb, { layers: ["pipes-base"] }).map(f => f.properties.i))];
      if (small && ids.length) toggleSelect(ids[0]); else if (ids.length) addSelect(ids.slice(0, 5000));
    };
    window.addEventListener("mousemove", move); window.addEventListener("mouseup", up, true);
  }, true);
}

async function loadGeometry(c) {
  if (!geoCache[c]) {
    $("#loading").hidden = false;
    geoCache[c] = await api(`/api/geometry/${c}`);
    const byI = new Array(geoCache[c].pipes.features.length);
    for (const f of geoCache[c].pipes.features) byI[f.properties.i] = f;
    geoCache[c].byI = byI;
  }
  geo = geoCache[c];
  state.geoCase = c; state.pipeFeatures = geo.pipes.features.length;
}
async function pushGeometry(fit) {
  await mapLoaded;
  paintColours(false);
  map.getSource("pipes").setData(geo.pipes);
  map.getSource("nodes").setData(geo.nodes);
  if (fit) { const b = geo.bounds; map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 30, animate: false }); }
  await new Promise(res => {
    const chk = () => { if (map.isSourceLoaded("pipes")) res(); else map.once("sourcedata", chk); };
    setTimeout(res, 20000); chk();
  });
  $("#loading").hidden = true; state.ready = true;
}
/* write colour, width, flags into the GeoJSON properties */
function paintColours(push = true) {
  if (!geo || !state.results) return;
  const cols = state.results.columns, by = state.colorBy, fs = geo.pipes.features;
  for (const f of fs) {
    const p = f.properties, k = p.i;
    p.c = colourOf(by, cols, k); p.w = widthOf(cols.dn_mm[k]);
    p.fail = (cols.over_limit[k] || cols.over_3ms[k]) ? 1 : 0; p.relay = cols.needs_relay[k] ? 1 : 0;
    p.dn = cols.dn_mm[k];
  }
  renderLegend();
  if (push && map.getSource("pipes")) map.getSource("pipes").setData(geo.pipes);
}
function drawSelection() {
  if (!map || !map.getSource("sel") || !geo) return;
  map.getSource("sel").setData({ type: "FeatureCollection", features: state.selected.map(i => geo.byI[i]).filter(Boolean) });
}
function zoomToPipes(ids) {
  let b = null;
  for (const i of ids) for (const [x, y] of geo.byI[i].geometry.coordinates) {
    b = b ? [Math.min(b[0], x), Math.min(b[1], y), Math.max(b[2], x), Math.max(b[3], y)] : [x, y, x, y];
  }
  if (b) map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 120, maxZoom: 18, duration: 400 });
}

/* ------------------------------------------------------------------ status line */
function setStatus(s, verb) {
  const el = $("#status-line"); if (!s) { el.textContent = "–"; return; }
  state.summary = s; state.lastSeconds = s.seconds;
  el.dataset.relay = s.needs_relay; el.dataset.seconds = s.seconds; el.dataset.pipes = s.pipes;
  const cls = (n, c) => n > 0 ? ` class="${c}"` : "";
  el.innerHTML = `${verb} <b>${fmt(s.pipes)} pipes</b> in <b id="st-seconds">${s.seconds.toFixed(2)}</b> s · <b>${fmt(s.km, 1)}</b> km · ` +
    `over limit <b id="st-over"${cls(s.over_limit, "bad")}>${fmt(s.over_limit)}</b> · over 3 m/s <b id="st-3ms"${cls(s.over_3ms, "bad")}>${fmt(s.over_3ms)}</b> · ` +
    `<b id="st-under">${fmt(s.km_under075_2031, 2)}</b> km under 0.75 m/s at 2031 · needs re-lay <b id="st-relay"${cls(s.needs_relay, "warn")}>${fmt(s.needs_relay)}</b>`;
}
function updateButtons() {
  const s = current();
  $("#undo-btn").disabled = !s || !s.can_undo; $("#redo-btn").disabled = !s || !s.can_redo;
  $("#copy-btn").disabled = !s;
  $("#readonly-hint").hidden = !s || !s.read_only;
  for (const f of ["gpkg", "dxf", "csv"]) $(`#export-${f}`).href = s ? `/api/scenarios/${encodeURIComponent(s.id)}/export.${f}` : "#";
}

/* ------------------------------------------------------------------ scenarios */
async function loadScenarios() {
  state.scenarios = await api("/api/scenarios");
  const sel = $("#scenario-select"), cmp = $("#compare-select");
  sel.innerHTML = state.scenarios.map(s => `<option value="${esc(s.id)}">${esc(s.read_only ? s.name : `${s.name} [what-if, ${s.edits} edit${s.edits === 1 ? "" : "s"}]`)}</option>`).join("");
  sel.value = state.sid;
  cmp.innerHTML = `<option value="">Compare with…</option>` + state.scenarios.filter(s => s.id !== state.sid).map(s => `<option value="${esc(s.id)}">${esc(s.name)}</option>`).join("");
  updateButtons();
}
async function fetchResults() {
  const r = await api(`/api/scenarios/${encodeURIComponent(state.sid)}/results`);
  state.results = r; return r;
}
async function selectScenario(sid) {
  state.sid = sid; state.selected = []; state.props = null;
  await loadScenarios();
  const c = current().case;
  const [res] = await Promise.all([fetchResults(), state.geoCase === c ? null : loadGeometry(c)]);
  setStatus(res.summary, "solved");
  if (state.pushedCase !== c) { const first = state.pushedCase == null; state.pushedCase = c; await pushGeometry(first); }
  else { paintColours(true); }
  state.case = c;
  drawSelection(); renderProps(); buildResults(); $("#loading").hidden = true;
}
async function refreshAfterEdit(summ, verb) {
  await Promise.all([fetchResults(), loadScenarios()]);
  setStatus({ ...state.results.summary, seconds: summ ? summ.seconds : state.results.summary.seconds }, verb);
  paintColours(true); buildResults(); await renderProps();
  if ($("#pane-profile").classList.contains("active") && $("#profile-start").value) drawProfile();
}
async function copyScenario() {
  const s = await post(`/api/scenarios/${encodeURIComponent(state.sid)}/copy`, {});
  await selectScenario(s.id);
}
async function applyEdit(field, value) {
  if (readOnly() || !state.selected.length || value === "" || Number.isNaN(Number(value))) return;
  try {
    const summ = await post(`/api/scenarios/${encodeURIComponent(state.sid)}/edits`, { target: "pipe", ids: state.selected, field, value: Number(value) });
    await refreshAfterEdit(summ, "re-solved");
  } catch (e) { toast("Edit refused: " + e.message); await renderProps(); }
}
async function undoRedo(kind) {
  const summ = await post(`/api/scenarios/${encodeURIComponent(state.sid)}/${kind}`);
  await refreshAfterEdit(summ, "re-solved");
}

/* ------------------------------------------------------------------ selection and properties */
async function selectPipe(i, opts = {}) {
  i = Number(i);
  state.selected = opts.add ? (state.selected.includes(i) ? state.selected : [...state.selected, i]) : [i];
  drawSelection(); if (opts.zoom) zoomToPipes([i]);
  await renderProps(); markRows();
  const cur = state.props && state.props.i === i ? state.props : null;
  if (cur) $("#profile-start").value = cur.from_mh;
  if ($("#pane-profile").classList.contains("active")) drawProfile();
}
async function toggleSelect(i) {
  const k = state.selected.indexOf(i);
  if (k >= 0) state.selected.splice(k, 1); else state.selected.push(i);
  drawSelection(); await renderProps(); markRows();
}
async function addSelect(ids) {
  state.selected = [...new Set([...state.selected, ...ids])];
  drawSelection(); await renderProps(); markRows();
}
async function renderProps() {
  const el = $("#props"), sel = state.selected;
  if (!sel.length) { el.innerHTML = `<p class="muted">Select a pipe on the map or in the Results table.</p>`; state.props = null; return; }
  const ro = readOnly(), cols = state.results.columns;
  let rows = "", head = "";
  const dnCtl = cur => {
    const opts = DN_CATALOGUE.slice(); if (cur != null && !opts.includes(cur)) opts.push(cur), opts.sort((a, b) => a - b);
    return `<select id="prop-dn" data-testid="prop-dn" ${ro ? "disabled" : ""}>${cur == null ? `<option value="">mixed</option>` : ""}${opts.map(o => `<option value="${o}" ${o === cur ? "selected" : ""}>${o}</option>`).join("")}</select>`;
  };
  if (sel.length === 1) {
    const i = sel[0];
    let p;
    try { p = await api(`/api/scenarios/${encodeURIComponent(state.sid)}/pipes/${i}`); } catch (e) { toast(e.message); return; }
    if (state.selected.length !== 1 || state.selected[0] !== i) return;   // selection moved while fetching
    state.props = p;
    head = `<p><b>${esc(p.label)}</b> <span class="muted">(row ${p.i}, ${esc(p.kind)}, ${esc(p.section)})</span></p>`;
    const num = (k, d) => `<tr><td>${k.label}</td><td>${fmt(p[k.key], d)}${k.unit ? " " + k.unit : ""}</td></tr>`;
    rows += `<tr><td>Size DN (mm)</td><td>${dnCtl(p.dn_mm)}</td></tr>`;
    rows += `<tr><td>Gradient (%)</td><td><input id="prop-s" data-testid="prop-s" type="number" step="0.01" min="0" value="${Number(p.s_pc).toFixed(3)}" ${ro ? "disabled" : ""}></td></tr>`;
    for (const [lab, key, d, unit] of [["Length", "length_m", 1, "m"], ["Flow, design year", "q_ls", 2, "L/s"], ["Velocity", "v_ms", 2, "m/s"], ["d/D", "d_over_D", 3, ""], ["d/D limit", "limit", 2, ""],
      ["Flow at 2031", "q2031_ls", 2, "L/s"], ["Velocity at 2031", "v2031_ms", 2, "m/s"], ["Depth up", "depth_up_m", 2, "m"], ["Depth down", "depth_dn_m", 2, "m"]])
      rows += `<tr><td>${lab}</td><td>${fmt(p[key], d)}${unit ? " " + unit : ""}</td></tr>`;
    const flag = (lab, v) => `<tr><td>${lab}</td><td class="${v ? "flag-bad" : ""}">${v ? "yes" : "no"}</td></tr>`;
    rows += flag("Over d/D limit", p.over_limit) + flag("Over 3 m/s", p.over_3ms) + flag("Under 0.75 m/s at 2031", p.under075) + flag("Needs re-lay", p.needs_relay);
    rows += `<tr><td>From manhole</td><td>${esc(p.from_mh)}</td></tr><tr><td>To manhole</td><td>${esc(p.to_mh)}</td></tr>`;
  } else {
    state.props = null;
    const dns = new Set(sel.map(i => cols.dn_mm[i])), ss = new Set(sel.map(i => Number(cols.s_pc[i]).toFixed(3)));
    const labels = sel.slice(0, 6).map(i => geo.byI[i].properties.label);
    head = `<p><b>${fmt(sel.length)} pipes selected</b> <span class="muted">${esc(labels.join(", "))}${sel.length > 6 ? ", …" : ""}</span></p><p class="muted">An edit applies to all of them.</p>`;
    rows += `<tr><td>Size DN (mm)</td><td>${dnCtl(dns.size === 1 ? [...dns][0] : null)}</td></tr>`;
    rows += `<tr><td>Gradient (%)</td><td><input id="prop-s" data-testid="prop-s" type="number" step="0.01" min="0" ${ss.size === 1 ? `value="${[...ss][0]}"` : `placeholder="mixed"`} ${ro ? "disabled" : ""}></td></tr>`;
  }
  el.innerHTML = `${head}<table>${rows}</table><p><button id="clear-sel" data-testid="clear-sel">Clear selection</button></p>`;
  $("#clear-sel").onclick = () => { state.selected = []; drawSelection(); renderProps(); markRows(); };
  const dn = $("#prop-dn"), s = $("#prop-s");
  dn.addEventListener("change", () => dn.value && applyEdit("dn_mm", dn.value));
  s.addEventListener("change", () => applyEdit("s_pc", s.value));
  s.addEventListener("keydown", e => { if (e.key === "Enter") s.blur(); });
}

/* ------------------------------------------------------------------ results table */
const RCOLS = [["label", "Label"], ["dn_mm", "DN"], ["q_ls", "Q L/s"], ["v_ms", "v m/s"], ["v2031_ms", "v 2031"], ["d_over_D", "d/D"], ["flags", "Flags"]];
function buildResults() {
  if (!state.results || !geo) return;
  const th = $("#results-table thead");
  th.innerHTML = "<tr>" + RCOLS.map(([k, l]) => `<th data-col="${k}">${l}${state.sort.col === k ? (state.sort.dir > 0 ? " ▲" : " ▼") : ""}</th>`).join("") + "</tr>";
  $$("th", th).forEach(h => h.onclick = () => { const c = h.dataset.col; state.sort = { col: c, dir: state.sort.col === c ? -state.sort.dir : 1 }; state.shown = 200; buildResults(); });
  const cols = state.results.columns, f = $("#results-filter").value.trim().toLowerCase(), n = geo.pipes.features.length;
  let idx = [];
  for (let i = 0; i < n; i++) if (!f || geo.byI[i].properties.label.toLowerCase().includes(f)) idx.push(i);
  const { col, dir } = state.sort;
  const key = col === "label" ? i => geo.byI[i].properties.label : col === "flags" ? i => (cols.over_limit[i] ? 4 : 0) + (cols.over_3ms[i] ? 2 : 0) + (cols.needs_relay[i] ? 1 : 0) : col === "i" ? i => i : i => cols[col][i];
  idx.sort((a, b) => { const x = key(a), y = key(b); return (x < y ? -1 : x > y ? 1 : 0) * dir; });
  state.rows = idx; drawRows();
}
function drawRows() {
  const cols = state.results.columns, tb = $("#results-table tbody"), part = state.rows.slice(0, state.shown);
  tb.innerHTML = part.map(i => {
    const fl = (cols.over_limit[i] ? `<span class="flag">d/D</span>` : "") + (cols.over_3ms[i] ? `<span class="flag">&gt;3</span>` : "") +
      (cols.under075[i] ? `<span class="flag b">&lt;0.75</span>` : "") + (cols.needs_relay[i] ? `<span class="flag o">re-lay</span>` : "");
    return `<tr data-i="${i}" class="${state.selected.includes(i) ? "sel" : ""}"><td>${esc(geo.byI[i].properties.label)}</td><td>${cols.dn_mm[i]}</td><td>${fmt(cols.q_ls[i], 1)}</td><td>${fmt(cols.v_ms[i], 2)}</td><td>${fmt(cols.v2031_ms[i], 2)}</td><td>${fmt(cols.d_over_D[i], 2)}</td><td>${fl}</td></tr>`;
  }).join("");
  $("#results-count").textContent = `${fmt(part.length)} of ${fmt(state.rows.length)} pipes`;
  $("#results-more").hidden = state.rows.length <= state.shown;
}
function markRows() { $$("#results-table tbody tr").forEach(r => r.classList.toggle("sel", state.selected.includes(Number(r.dataset.i)))); }

/* ------------------------------------------------------------------ profile */
async function drawProfile() {
  const start = $("#profile-start").value.trim(), end = $("#profile-end").value.trim(), svg = $("#profile-svg");
  if (!start) { svg.innerHTML = ""; $("#profile-info").textContent = "Select a pipe first."; return; }
  let rows;
  try { rows = await api(`/api/scenarios/${encodeURIComponent(state.sid)}/profile?start=${encodeURIComponent(start)}` + (end ? `&end=${encodeURIComponent(end)}` : "")); }
  catch (e) { toast("Profile: " + e.message); return; }
  if (!rows.length) { svg.innerHTML = ""; $("#profile-info").textContent = "No pipes downstream."; return; }
  const W = svg.clientWidth || 900, H = svg.clientHeight || 200, L = 56, R = 16, T = 12, B = 48;
  const x0 = Math.min(...rows.map(r => r.ch0)), x1 = Math.max(...rows.map(r => r.ch1));
  const ys = rows.flatMap(r => [r.ground0, r.ground1, r.inv0, r.inv1, r.crown0, r.crown1, r.water0, r.water1]).filter(v => v != null);
  let y0 = Math.min(...ys), y1 = Math.max(...ys); const m = (y1 - y0) * 0.05 || 1; y0 -= m; y1 += m;
  const X = v => L + (v - x0) / ((x1 - x0) || 1) * (W - L - R), Y = v => T + (y1 - v) / (y1 - y0) * (H - T - B);
  let s = `<rect x="${L}" y="${T}" width="${W - L - R}" height="${H - T - B}" fill="#fbfcfd" stroke="#d5d9df"/>`;
  const ticks = (a, b, n) => { const step = (b - a) / n, mag = 10 ** Math.floor(Math.log10(step)), nice = [1, 2, 5, 10].map(k => k * mag).find(k => k >= step); const out = []; for (let v = Math.ceil(a / nice) * nice; v <= b; v += nice) out.push(v); return out; };
  for (const t of ticks(y0, y1, 5)) s += `<line x1="${L}" x2="${W - R}" y1="${Y(t)}" y2="${Y(t)}" stroke="#eceff2"/><text x="${L - 4}" y="${Y(t) + 4}" text-anchor="end">${fmt(t, 1)}</text>`;
  for (const t of ticks(x0, x1, 8)) s += `<line y1="${T}" y2="${H - B}" x1="${X(t)}" x2="${X(t)}" stroke="#eceff2"/><text x="${X(t)}" y="${H - B + 14}" text-anchor="middle">${fmt(t, 0)}</text>`;
  s += `<text x="${(L + W - R) / 2}" y="${H - 18}" text-anchor="middle">chainage (m)</text><text transform="translate(12 ${(T + H - B) / 2}) rotate(-90)" text-anchor="middle">level (m)</text>`;
  const line = (a, b, col, wd, dash) => `<polyline fill="none" stroke="${col}" stroke-width="${wd}" ${dash ? `stroke-dasharray="${dash}"` : ""} points="${rows.map(r => `${X(r.ch0)},${Y(r[a + "0"])} ${X(r.ch1)},${Y(r[a + "1"])}`).join(" ")}"/>`;
  s += line("ground", 0, "#7a6a4f", 1.6);
  s += line("water", 0, "#3b8bd4", 1.4, "4 2");
  for (const r of rows) {
    const col = r.needs_relay ? "#e6821e" : "#8aa4bd";
    s += `<polygon class="pipe-seg${r.needs_relay ? " relay" : ""}" data-pipe="${esc(r.pipe)}" fill="${col}" fill-opacity=".55" stroke="${r.needs_relay ? "#c4620a" : "#34506b"}" stroke-width="1" points="${X(r.ch0)},${Y(r.inv0)} ${X(r.ch1)},${Y(r.inv1)} ${X(r.ch1)},${Y(r.crown1)} ${X(r.ch0)},${Y(r.crown0)}"><title>${esc(r.pipe)} DN${r.dn_mm}, v ${fmt(r.v_ms, 2)} m/s${r.needs_relay ? ", needs re-lay" : ""}</title></polygon>`;
  }
  s += rows.map((r, k) => (k === 0 || (r.ch1 - x0) / ((x1 - x0) || 1) * (W - L - R) > 0 && k % Math.max(1, Math.ceil(rows.length / 12)) === 0) ? `<line x1="${X(r.ch0)}" x2="${X(r.ch0)}" y1="${Y(r.ground0)}" y2="${Y(r.inv0)}" stroke="#555" stroke-width=".8"/><text x="${X(r.ch0)}" y="${Y(r.ground0) - 3}" text-anchor="middle" font-size="9">${esc(r.from_mh)}</text>` : "").join("");
  s += `<g transform="translate(${W - R - 250} ${H - 4})"><text fill="#7a6a4f">— ground</text><text x="70" fill="#3b8bd4">— water (peak)</text><text x="170" fill="#34506b">— pipe (orange = re-lay)</text></g>`;
  svg.setAttribute("viewBox", `0 0 ${W} ${H}`); svg.innerHTML = s;
  const km = (x1 - x0) / 1000, rl = rows.filter(r => r.needs_relay).length;
  $("#profile-info").textContent = `${rows.length} pipes, ${fmt(x1 - x0, 0)} m, to ${rows[rows.length - 1].to_mh}${rl ? `, ${rl} need re-lay (orange)` : ""}`;
}

/* ------------------------------------------------------------------ tools, tables */
function tableHTML(rows, id) {
  if (!rows || !rows.length) return `<p class="muted" style="padding:8px 10px">No rows.</p>`;
  const cols = Object.keys(rows[0]);
  return `<table class="grid" ${id ? `id="${id}" data-testid="${id}"` : ""}><thead><tr>${cols.map(c => `<th>${esc(c)}</th>`).join("")}</tr></thead><tbody>` +
    rows.map(r => `<tr>${cols.map(c => { const v = r[c]; return `<td>${typeof v === "number" ? fmt(v, Number.isInteger(v) ? 0 : 3) : typeof v === "boolean" ? (v ? "yes" : "") : esc(v && typeof v === "object" ? JSON.stringify(v) : v)}</td>`; }).join("")}</tr>`).join("") + `</tbody></table>`;
}
function renderResult(res) {
  if (Array.isArray(res)) return tableHTML(res, "tool-table");
  let h = "", chips = [], rest = {};
  for (const [k, v] of Object.entries(res)) {
    if (k === "rows" && Array.isArray(v)) continue;
    if (v !== null && typeof v === "object") rest[k] = v; else chips.push(`<span><b>${esc(k)}</b>: ${esc(typeof v === "number" ? fmt(v, Number.isInteger(v) ? 0 : 3) : v)}</span>`);
  }
  if (chips.length) h += `<div class="kv">${chips.join("")}</div>`;
  if (res.rows) h += tableHTML(res.rows, "tool-table");
  if (Object.keys(rest).length) h += `<pre class="json">${esc(JSON.stringify(rest, null, 1))}</pre>`;
  return h || `<p class="muted" style="padding:8px 10px">Empty result.</p>`;
}
function buildToolsMenu() {
  const groups = {};
  for (const t of state.tools) (groups[t.menu] = groups[t.menu] || []).push(t);
  $("#tools-list").innerHTML = Object.entries(groups).map(([m, ts]) => `<div class="head">${esc(m)}</div>` +
    ts.map(t => `<button class="item" data-tool="${esc(t.name)}" data-testid="tool-${esc(t.name)}" title="${esc(t.script)} (${esc(t.seconds)} s)">${esc(t.label)}<span class="muted"> · ${esc(t.seconds)} s</span></button>`).join("")).join("");
  $$("#tools-list button.item").forEach(b => b.onclick = () => { closeMenus(); runTool(b.dataset.tool); });
}
async function runTool(name) {
  const t = state.tools.find(x => x.name === name), slow = /\d{2}/.test(t.seconds);
  showTab("pane-tool");
  $("#tool-title").textContent = t.label; $("#tool-meta").textContent = "running…";
  if (slow) busy(true, `Running "${t.label}" (about ${t.seconds} s)…`);
  const t0 = performance.now();
  try {
    const res = await post(`/api/tools/${encodeURIComponent(name)}?sid=${encodeURIComponent(state.sid)}`);
    $("#tool-output").innerHTML = renderResult(res);
    $("#tool-meta").textContent = `${((performance.now() - t0) / 1000).toFixed(1)} s · scenario ${state.sid}`;
    $("#tool-output").dataset.tool = name;
  } catch (e) { $("#tool-output").innerHTML = `<p style="padding:8px 10px;color:#c0392b">${esc(e.message)}</p>`; $("#tool-meta").textContent = "failed"; }
  finally { busy(false); }
}
async function runCompare(other) {
  if (!other) return;
  showTab("pane-compare");
  try {
    const c = await api(`/api/compare?a=${encodeURIComponent(state.sid)}&b=${encodeURIComponent(other)}`);
    $("#compare-title").textContent = `${state.sid} vs ${other}: ${fmt(c.changed)} pipes changed`;
    const keys = ["pipes", "km", "over_limit", "over_3ms", "km_under075_2031", "needs_relay"];
    const sum = `<table class="grid" style="width:auto;margin:6px 10px" data-testid="compare-summary"><thead><tr><th></th><th>${esc(state.sid)}</th><th>${esc(other)}</th></tr></thead><tbody>` +
      keys.map(k => `<tr><td>${k}</td><td>${fmt(c.a[k], 2).replace(/\.00$/, "")}</td><td>${fmt(c.b[k], 2).replace(/\.00$/, "")}</td></tr>`).join("") + `</tbody></table>`;
    $("#compare-output").innerHTML = sum + tableHTML(c.rows, "compare-table");
  } catch (e) { toast("Compare: " + e.message); }
}

/* ------------------------------------------------------------------ assistant */
function md(t) {
  let h = esc(t).replace(/```([\s\S]*?)```/g, (_, c) => `<pre>${c}</pre>`).replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<b>$1</b>");
  h = h.replace(/(^|\n)[-*] (.+)/g, "$1&bull; $2");
  return h.replace(/\n/g, "<br>");
}
function addMsg(role, html, meta) {
  const d = document.createElement("div"); d.className = `msg ${role}`; d.innerHTML = html + (meta ? `<div class="meta">${meta}</div>` : "");
  const log = $("#assistant-log"); log.appendChild(d); log.scrollTop = log.scrollHeight; return d;
}
async function initAssistant() {
  try { state.assistant = await api("/api/assistant/status"); }
  catch (e) { state.assistant = { available: false, reason: "The assistant service is not reachable." }; }
  $("#assistant-status").textContent = state.assistant.available ? `Assistant ready (${state.assistant.model}). It works on scenario: ${state.sid || "–"}` : `Assistant unavailable: ${state.assistant.reason || "no key set"}. The rest of the app is not affected.`;
  $("#assistant-input").disabled = $("#assistant-send").disabled = !state.assistant.available;
  $("#assistant-form").addEventListener("submit", async e => {
    e.preventDefault();
    const inp = $("#assistant-input"), msg = inp.value.trim(); if (!msg || !state.assistant.available) return;
    inp.value = ""; addMsg("user", md(msg)); $("#assistant-send").disabled = true;
    const wait = addMsg("bot", `<span class="muted">thinking…</span>`);
    try {
      const r = await post("/api/assistant", { sid: state.sid, message: msg, history: state.history });
      state.history.push({ role: "user", content: msg }, { role: "assistant", content: r.reply });
      const calls = (r.tool_calls || []).map(c => `<code>${esc(c.name)}</code>(${esc(JSON.stringify(c.input))}) ${c.ok ? "ok" : "failed"}`).join("<br>");
      const u = r.usage ? `tokens: ${fmt(r.usage.input_tokens)} in, ${fmt(r.usage.output_tokens)} out` : "";
      wait.remove();
      addMsg("bot", md(r.reply), `${calls ? `<div class="toolcalls" data-testid="tool-calls">Tool calls:<br>${calls}</div>` : ""}${u}`);
      // the assistant may have edited a what-if: refresh from the server
      await loadScenarios(); await fetchResults(); setStatus(state.results.summary, "solved"); paintColours(true); buildResults();
    } catch (err) { wait.innerHTML = `<span style="color:#c0392b">${esc(err.message)}</span>`; }
    finally { $("#assistant-send").disabled = false; }
  });
}

/* ------------------------------------------------------------------ chrome */
function showTab(pane) {
  $$(".tab").forEach(t => t.classList.toggle("active", t.dataset.pane === pane));
  $$(".pane").forEach(p => p.classList.toggle("active", p.id === pane));
  if (pane === "pane-profile" && state.props) { $("#profile-start").value = state.props.from_mh; drawProfile(); }
}
function closeMenus() { $("#export-list").hidden = true; $("#tools-list").hidden = true; }

async function init() {
  initMap();
  $$(".tab").forEach(t => t.onclick = () => showTab(t.dataset.pane));
  $("#export-btn").onclick = e => { e.stopPropagation(); const h = $("#export-list").hidden; closeMenus(); $("#export-list").hidden = !h; };
  $("#tools-menu").onclick = e => { e.stopPropagation(); const h = $("#tools-list").hidden; closeMenus(); $("#tools-list").hidden = !h; };
  document.addEventListener("click", closeMenus);
  $$("#export-list a").forEach(a => a.addEventListener("click", () => setTimeout(closeMenus, 50)));
  $("#scenario-select").onchange = e => selectScenario(e.target.value).catch(x => toast(x.message));
  $("#copy-btn").onclick = () => copyScenario().catch(x => toast(x.message));
  $("#undo-btn").onclick = () => undoRedo("undo").catch(x => toast(x.message));
  $("#redo-btn").onclick = () => undoRedo("redo").catch(x => toast(x.message));
  $("#compare-select").onchange = e => { runCompare(e.target.value); };
  $("#color-by").onchange = e => { state.colorBy = e.target.value; paintColours(true); };
  $("#results-filter").oninput = () => { state.shown = 200; buildResults(); };
  $("#results-more").onclick = () => { state.shown += 200; drawRows(); };
  $("#results-table tbody").addEventListener("click", e => { const tr = e.target.closest("tr"); if (tr) selectPipe(tr.dataset.i, { zoom: true }); });
  $("#profile-run").onclick = () => drawProfile();
  window.addEventListener("resize", () => { if ($("#pane-profile").classList.contains("active")) drawProfile(); });
  try { state.tools = await api("/api/tools"); buildToolsMenu(); } catch (e) { toast("Tools: " + e.message); }
  const sc = await api("/api/scenarios");
  state.sid = sc[0].id;
  await selectScenario(state.sid);
  initAssistant();
}
window.app = { state, selectPipe, selectScenario, runTool, drawProfile, showTab, get map() { return map; } };
init().catch(e => { console.error(e); $("#status-line").textContent = "Error: " + e.message; $("#loading").textContent = "Error: " + e.message; });
