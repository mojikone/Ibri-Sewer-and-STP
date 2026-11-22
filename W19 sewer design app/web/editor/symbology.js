/* Symbology: colour coding and labels for every element type, kept as named definitions with the project.
   The concepts follow SewerGEMS's Element Symbology as its public help describes it (a list of colour codings and
   annotations per element type; any attribute, a calculated range, steps, a colour ramp, colour and/or size, an
   above-range class, prefix and suffix with units, free-form text, several annotations per type, named definitions).
   Nothing here comes from SewerGEMS's files. Loaded before editor.js; its functions use the editor's globals only when
   they are called. */
"use strict";

const SYM_TYPES = { links: "Pipes", nodes: "Structures", catchments: "Catchments" };
const SYM_TABLE = { links: "links", nodes: "nodes", catchments: "catchments" };

/* ---- the fields each element type can be coloured or labelled by: [key, label, unit, group, kind] */
const SYM_FIELDS = {
  links: [
    ["id", "ID", "", "Input", "text"], ["kind", "Type", "", "Input", "text"], ["size", "Size or section", "", "Input", "text"],
    ["dn_mm", "Size DN", "mm", "Input", "num"], ["length_m", "Length", "m", "Input", "num"], ["s_pc", "Gradient", "%", "Input", "num"],
    ["up_inv", "Upstream invert", "m", "Input", "num"], ["dn_inv", "Downstream invert", "m", "Input", "num"],
    ["depth_up", "Depth at upstream end", "m", "Input", "num"], ["depth_dn", "Depth at downstream end", "m", "Input", "num"],
    ["depth_max", "Depth, deeper end", "m", "Input", "num"], ["from_node", "From node", "", "Input", "text"], ["to_node", "To node", "", "Input", "text"],
    ["q_ls", "Flow", "L/s", "Results", "num"], ["v_ms", "Velocity", "m/s", "Results", "num"], ["d_over_D", "d/D (depth/rise)", "", "Results", "num"],
    ["limit", "d/D limit", "", "Results", "num"], ["depth_m", "Normal depth (sections)", "m", "Results", "num"],
    ["yc_m", "Critical depth (sections)", "m", "Results", "num"], ["q_full_ls", "Full capacity (sections)", "L/s", "Results", "num"],
    ["flags", "Failed checks", "", "Results", "text"],
    ["storm_q", "Storm flow (peak or at the slider)", "m3/s", "Storm", "num"], ["storm_cap", "Storm fullness (peak or at the slider)", "", "Storm", "num"],
  ],
  nodes: [
    ["id", "ID", "", "Input", "text"], ["kind", "Type", "", "Input", "text"], ["ground", "Ground level", "m", "Input", "num"],
    ["invert", "Invert", "m", "Input", "num"], ["depth", "Depth (ground - invert)", "m", "Input", "num"],
    ["load", "Load, design set", "m3/d", "Input", "num"], ["inflow_m3d", "Fixed inflow", "m3/d", "Input", "num"],
    ["storm_head", "Storm peak head", "m", "Storm", "num"], ["storm_flood", "Storm flooding (peak or at the slider)", "m3/s", "Storm", "num"],
  ],
  catchments: [
    ["id", "ID", "", "Input", "text"], ["outlet", "Outlet", "", "Input", "text"], ["area_ha", "Area", "ha", "Input", "num"],
    ["imperv_pc", "Impervious", "%", "Input", "num"], ["width_m", "Width", "m", "Input", "num"], ["slope_pc", "Slope", "%", "Input", "num"],
  ],
};
const symField = (type, k) => SYM_FIELDS[type].find(f => f[0] === k) || [k, k, "", "", "num"];

/* ---- default definition: what the map showed before symbology existed, so nothing changes until the engineer does */
function symDefaultDef() {
  return {
    links: { codings: [], color: null, labels: { size: 10.5, minzoom: 17, overlap: true, items: [{ on: true, field: "size" }, { on: true, field: "s_pc", prefix: " · ", suffix: " %", dec: 2, same: true }] } },
    nodes: { codings: [], color: null, labels: { size: 11, minzoom: 15.5, items: [{ on: true, field: "id" }] } },
    catchments: { codings: [], color: null, labels: { size: 11, minzoom: 14, items: [{ on: false, field: "id" }] } },
  };
}
function symDefault() { return { active: "Default", defs: { Default: symDefaultDef() } }; }
const symDef = () => (state.sym && state.sym.defs[state.sym.active]) || symDefaultDef();

/* ---- values: one context per redraw (results, storm, loads), then a getter per element */
function symContext() {
  const m = state.model, S = typeof stormNow === "function" ? stormNow() : null;
  const FR = state.stormFrame && state.stormFrame.sid === state.sid ? state.stormFrame : null;
  return { m, R: srcLinks(), E: state.results ? state.results.links : {}, S, FR, loads: (m.loads || {})[m.settings.design_load] || {} };
}
function symValue(type, f, k, c) {
  const p = f.properties, id = String(f.id);
  if (k === "id") return id;
  if (type === "links") {
    const r = c.R[id] || {}, e = c.E[id] || {};
    const n0 = c.m.nodes.get(String(p.from_node)), n1 = c.m.nodes.get(String(p.to_node));
    const g0 = n0 && n0.properties.ground, g1 = n1 && n1.properties.ground;
    switch (k) {
      case "size": return p.kind === "pump" ? "pump" : p.section ? String(p.section) : `DN${p.dn_mm ?? "?"}`;
      case "s_pc": return p.kind === "pump" || !(p.length_m > 0) ? (e.s_pc ?? null) : (p.up_inv - p.dn_inv) / p.length_m * 100;
      case "depth_up": return g0 != null && p.up_inv != null ? g0 - p.up_inv : null;
      case "depth_dn": return g1 != null && p.dn_inv != null ? g1 - p.dn_inv : null;
      case "depth_max": { const a = symValue(type, f, "depth_up", c), b = symValue(type, f, "depth_dn", c); return a == null ? b : b == null ? a : Math.max(a, b); }
      case "flags": return ["over_limit", "over_vmax", "surcharged", "negative_slope", "under_vmin"].filter(x => r[x]).join(", ") || "none";
      case "storm_q": return c.FR ? (c.FR.links[id] == null ? null : Math.abs(c.FR.links[id])) : c.S && c.S.links[id] ? c.S.links[id].q_peak : null;
      case "storm_cap": return c.FR ? (c.FR.links[id] ?? null) : c.S && c.S.links[id] ? c.S.links[id].capacity_peak : null;
    }
    if (k in r) return r[k];
    return p[k] ?? null;
  }
  if (type === "nodes") {
    switch (k) {
      case "depth": return p.ground != null && p.invert != null ? p.ground - p.invert : null;
      case "load": return c.loads[id] ?? 0;
      case "storm_head": return c.S && c.S.nodes[id] ? c.S.nodes[id].head_peak : null;
      case "storm_flood": return c.FR ? (c.FR.flooding[id] ?? 0) : c.S && c.S.nodes[id] ? c.S.nodes[id].flooding_peak : null;
    }
    return p[k] ?? null;
  }
  return p[k] ?? null;
}

/* ---- colour coding: numeric classes "up to" a value (and one above the last), or one class per text value */
const SYM_RAMPS = {
  "Blue to red": ["#2166ac", "#67a9cf", "#d1e5f0", "#fddbc7", "#ef8a62", "#b2182b"],
  "Viridis": ["#440154", "#3b528b", "#21918c", "#5ec962", "#fde725"],
  "Blues": ["#c6dbef", "#6baed6", "#2171b5", "#08306b"],
  "Green to red": ["#1a9850", "#91cf60", "#fee08b", "#fc8d59", "#d73027"],
  "Purples": ["#dadaeb", "#9e9ac8", "#6a51a3", "#3f007d"],
};
const SYM_CATS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];
function symHex(c) { const n = parseInt(c.slice(1), 16); return [n >> 16 & 255, n >> 8 & 255, n & 255]; }
function symRampAt(stops, t) {
  if (stops.length === 1) return stops[0];
  const x = Math.min(Math.max(t, 0), 1) * (stops.length - 1), i = Math.min(Math.floor(x), stops.length - 2), u = x - i;
  const a = symHex(stops[i]), b = symHex(stops[i + 1]);
  return "#" + a.map((v, j) => Math.round(v + (b[j] - v) * u).toString(16).padStart(2, "0")).join("");
}
function symScope(cd, type) {
  const T = state.model[type === "links" ? "linkFeat" : type === "nodes" ? "nodeFeat" : "catchFeat"];
  if (cd.scope !== "ids") return T;
  const s = new Set((cd.ids || []).map(String)); return T.filter(f => s.has(String(f.id)));
}
function symValues(cd, type) {
  const c = symContext(); return symScope(cd, type).map(f => symValue(type, f, cd.field, c)).filter(v => v != null && v !== "" && !(typeof v === "number" && !isFinite(v)));
}
function symRange(cd, type) {
  const v = symValues(cd, type).filter(x => typeof x === "number"); if (!v.length) return null;
  return [Math.min(...v), Math.max(...v)];
}
const symRound = v => Math.abs(v) >= 100 ? Math.round(v) : +v.toPrecision(3);
function symRoundUp(v) {                                   // the same rounding, upwards
  const r = symRound(v); if (r >= v) return r;
  const step = Math.abs(v) >= 100 ? 1 : Math.pow(10, Math.floor(Math.log10(Math.abs(v) || 1)) - 2);
  return +(r + step).toPrecision(12);
}
/* classes from min to max in `steps` (equal widths, or equal counts), coloured along the ramp, sized 2 to 8 px */
function symInitialize(cd, type, opt) {
  const o = Object.assign({ steps: 5, method: "equal", ramp: "Blue to red", reverse: false, min: null, max: null }, opt || {});
  let stops = SYM_RAMPS[o.ramp] || SYM_RAMPS["Blue to red"]; if (o.reverse) stops = [...stops].reverse();
  if (symField(type, cd.field)[4] === "text") {
    const u = [...new Set(symValues(cd, type).map(String))].sort().slice(0, 30);
    cd.cats = u.map((v, i) => ({ value: v, color: SYM_CATS[i % SYM_CATS.length], size: 3 })); cd.breaks = []; return cd;
  }
  const r = symRange(cd, type), lo = o.min ?? (r ? r[0] : 0), hi = o.max ?? (r ? r[1] : 1), k = Math.max(1, Math.round(o.steps));
  let edges;
  if (o.method === "quantile") {
    const v = symValues(cd, type).filter(x => typeof x === "number" && x >= lo && x <= hi).sort((a, b) => a - b);
    edges = Array.from({ length: k }, (_, i) => v.length ? v[Math.min(v.length - 1, Math.floor((i + 1) * v.length / k) - 1)] : hi);
  } else edges = Array.from({ length: k }, (_, i) => lo + (hi - lo) * (i + 1) / k);
  edges = [...new Set(edges.map(symRound))];
  const top = edges[edges.length - 1];                     // rounded down, the largest value would fall above the range
  if (top < hi && o.method !== "quantile") edges[edges.length - 1] = symRoundUp(hi);
  cd.breaks = edges.map((to, i) => ({ to, color: symRampAt(stops, edges.length > 1 ? i / (edges.length - 1) : 0), size: +(2 + 6 * (edges.length > 1 ? i / (edges.length - 1) : 0)).toFixed(1) }));
  cd.above = cd.above || { color: "#7a0e3a", size: 9 }; cd.cats = [];
  return cd;
}
/* the class an element falls in: [index, colour, size], index -1 above the range, null when it has no value */
function symClass(cd, v) {
  if (v == null || v === "" || (typeof v === "number" && !isFinite(v))) return null;
  if (cd.cats && cd.cats.length) { const i = cd.cats.findIndex(x => x.value === String(v)); return i < 0 ? null : [i, cd.cats[i].color, cd.cats[i].size]; }
  for (let i = 0; i < (cd.breaks || []).length; i++) if (v <= cd.breaks[i].to) return [i, cd.breaks[i].color, cd.breaks[i].size];
  return cd.above ? [-1, cd.above.color, cd.above.size] : null;
}
function symRows(cd, type) {
  const f = symField(type, cd.field), u = f[2] ? ` ${f[2]}` : "";
  if (cd.cats && cd.cats.length) return cd.cats.map((x, i) => ({ i, label: x.value, color: x.color, size: x.size }));
  const rows = (cd.breaks || []).map((b, i) => ({ i, label: i === 0 ? `up to ${b.to}${u}` : `${cd.breaks[i - 1].to} - ${b.to}${u}`, color: b.color, size: b.size }));
  if (cd.above && cd.breaks && cd.breaks.length) rows.push({ i: -1, label: `over ${cd.breaks[cd.breaks.length - 1].to}${u}`, color: cd.above.color, size: cd.above.size });
  return rows;
}
const symStorm = () => ["links", "nodes"].some(t => { const cd = symActive(t); return !!cd && cd.field.startsWith("storm"); });
const symActive = type => {                               // pipes: only while Colour by is set to that coding
  const d = symDef()[type]; if (!d) return null;
  const id = type === "links" ? (state.colorBy && state.colorBy.startsWith("sym:") ? state.colorBy.slice(4) : null) : d.color;
  return id ? d.codings.find(x => x.id === id) || null : null;
};

/* ---- applied to the map features: _c (colour), _w (pipe width) / _r (node radius), _lab (label), _sc (class) */
function symApply() {
  const m = state.model; if (!m) return;
  const c = symContext(), def = symDef();
  for (const type of ["links", "nodes", "catchments"]) {
    const T = type === "links" ? m.linkFeat : type === "nodes" ? m.nodeFeat : m.catchFeat;
    const cd = symActive(type), inScope = cd && cd.scope === "ids" ? new Set((cd.ids || []).map(String)) : null;
    const L = def[type].labels;
    for (const f of T) {
      const p = f.properties;
      delete p._sc; if (type !== "links") delete p._c; delete p._w; delete p._r;
      if (cd && (!inScope || inScope.has(String(f.id)))) {
        const k = symClass(cd, symValue(type, f, cd.field, c));
        if (k) {
          p._sc = k[0];
          if (cd.mode !== "size") p._c = k[1];
          if (cd.mode !== "color") { if (type === "nodes") p._r = k[2]; else p._w = k[2]; }
        } else if (type === "links") p._c = GREY;
      }
      p._lab = symLabel(type, f, L, c);
    }
  }
  state.dirty.catch = true;
}
function symFormat(type, k, v, dec) {
  if (v == null) return "-";
  if (typeof v === "number") return dec != null && dec !== "" ? v.toFixed(+dec) : String(symRound(v));
  return String(v);
}
function symLabel(type, f, L, c) {
  let out = "";
  for (const it of (L && L.items) || []) {
    if (!it.on) continue;
    let s;
    if (it.template != null) s = it.template.replace(/\{(\w+)(?::(\d))?(:u)?\}/g, (_, k, d, u) => symFormat(type, k, symValue(type, f, k, c), d) + (u ? (symField(type, k)[2] ? " " + symField(type, k)[2] : "") : ""));
    else {
      if (type === "links" && it.field === "s_pc" && f.properties.kind === "pump") continue;                    // a pump has no gradient
      const unit = symField(type, it.field)[2];
      s = (it.prefix || "").replace(/%u/g, unit) + symFormat(type, it.field, symValue(type, f, it.field, c), it.dec) + (it.suffix || "").replace(/%u/g, unit);
    }
    out += out && !it.same ? "\n" + s : s;
  }
  return out;
}
/* pipe label points: the middle of each pipe (by length along it), turned to the pipe's direction and kept upright */
function symLabelPoints() {
  const m = state.model, F = [];
  for (const f of m.linkFeat) {
    const lab = f.properties._lab, c = f.geometry && f.geometry.coordinates; if (!lab || !c || c.length < 2) continue;
    const k = Math.cos((c[0][1] || 0) * Math.PI / 180), seg = [];
    let tot = 0; for (let i = 1; i < c.length; i++) { const d = Math.hypot((c[i][0] - c[i - 1][0]) * k, c[i][1] - c[i - 1][1]); seg.push(d); tot += d; }
    let half = tot / 2, i = 0; while (i < seg.length - 1 && half > seg[i]) { half -= seg[i]; i++; }
    const a = c[i], b = c[i + 1], u = seg[i] > 0 ? half / seg[i] : 0.5;
    let rot = Math.atan2(-(b[1] - a[1]), (b[0] - a[0]) * k) * 180 / Math.PI;               // screen degrees, clockwise
    if (rot > 90) rot -= 180; else if (rot < -90) rot += 180;
    F.push({ type: "Feature", properties: { _lab: lab, _rot: rot }, geometry: { type: "Point", coordinates: [a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u] } });
  }
  return { type: "FeatureCollection", features: F };
}
/* label layers follow the definition: text size and the zoom from which labels show */
function symLayers() {
  if (!map || !map.getLayer("links-label")) return;
  const def = symDef();
  for (const [type, layer] of [["links", "links-label"], ["nodes", "nodes-label"], ["catchments", "catch-label"]]) {
    const L = def[type].labels; if (!map.getLayer(layer)) continue;
    map.setLayoutProperty(layer, "text-size", +L.size || 11);
    map.setLayerZoomRange(layer, Math.max(0, Math.min(22, +L.minzoom || 0)), 24);
    const ov = L.overlap ?? (type === "links");                // pipe labels drawn even where they overlap (as SewerGEMS draws them)
    map.setLayoutProperty(layer, "text-allow-overlap", !!ov);
  }
}

/* ---- legend for the active codings, with counts; a row selects its elements */
function symLegend(type) {
  const cd = symActive(type); if (!cd) return "";
  const m = state.model, T = type === "links" ? m.linkFeat : type === "nodes" ? m.nodeFeat : m.catchFeat;
  const n = {}; for (const f of T) if (f.properties._sc != null) n[f.properties._sc] = (n[f.properties._sc] || 0) + 1;
  const f = symField(type, cd.field), sw = r => cd.mode === "size" ? `background:#4b5563;height:${Math.max(2, Math.min(10, r.size))}px` : `background:${r.color}` + (cd.mode === "both" ? `;height:${Math.max(2, Math.min(10, r.size))}px` : "");
  return `<div class="t">${esc(SYM_TYPES[type])}: ${esc(cd.name || f[1])}${f[2] ? ` (${esc(f[2])})` : ""}</div>` +
    symRows(cd, type).map(r => `<div class="r sym-row" data-type="${type}" data-i="${r.i}" data-testid="sym-legend-${type}-${r.i}" title="Click to select these"><span class="sw" style="${sw(r)}"></span>${esc(r.label)} <span class="muted">(${n[r.i] || 0})</span></div>`).join("");
}
function symSelectClass(type, i) {
  const m = state.model, T = type === "links" ? m.linkFeat : type === "nodes" ? m.nodeFeat : m.catchFeat;
  const ids = T.filter(f => f.properties._sc === i).map(f => String(f.id));
  if (ids.length) setSel(SYM_TABLE[type], ids, { zoom: false }); else toast("No element in that class.", "info");
}

/* ---- persistence: the definitions live with the project (saved in its file and its session snapshot) */
async function symLoad() {
  let s = null; try { s = await jget(`/projects/${state.pid}/symbology`); } catch (e) { /* none */ }
  state.sym = s && s.defs && Object.keys(s.defs).length ? s : symDefault();
  for (const d of Object.values(state.sym.defs)) for (const t of Object.keys(SYM_TYPES)) if (!d[t]) d[t] = symDefaultDef()[t];
  if (!state.sym.defs[state.sym.active]) state.sym.active = Object.keys(state.sym.defs)[0];
  symSyncSelects(); symLayers();
}
async function symSave() { if (state.pid) await jpost(`/projects/${state.pid}/symbology`, state.sym); }
/* after a change: colour the map again, relabel, redraw the legend and the Display card selects */
function symRefresh(save) {
  symSyncSelects(); mergeResults(); symLayers(); renderLegend(); pushMap(); if (typeof stormBar === "function") stormBar();
  if (save) enqueue(symSave);
}

/* ---- Display card: pipes "Colour by" lists the custom codings; structures and catchments have their own select */
function symSyncSelects() {
  const def = symDef(), cb = $("#color-by");
  if (cb) {
    for (const o of [...cb.querySelectorAll("option[data-sym]")]) o.remove();
    for (const cd of def.links.codings) { const o = document.createElement("option"); o.value = "sym:" + cd.id; o.dataset.sym = "1"; o.textContent = "custom: " + (cd.name || symField("links", cd.field)[1]); cb.appendChild(o); }
    if (def.links.color && def.links.codings.some(x => x.id === def.links.color)) state.colorBy = "sym:" + def.links.color;
    else if (state.colorBy.startsWith("sym:")) state.colorBy = "v_ms";
    cb.value = state.colorBy;
  }
  for (const [type, sel] of [["nodes", "#node-color-by"], ["catchments", "#catch-color-by"]]) {
    const s = $(sel); if (!s) continue;
    s.innerHTML = `<option value="">${type === "nodes" ? "type" : "plain"}</option>` + def[type].codings.map(cd => `<option value="${esc(cd.id)}">custom: ${esc(cd.name || symField(type, cd.field)[1])}</option>`).join("");
    s.value = def[type].color || "";
    const none = !def[type].codings.length; s.hidden = none;                     // shown once there is a custom coding to pick
    const lab = document.querySelector(`label[for="${s.id}"]`); if (lab) lab.hidden = none;
  }
  const ds = $("#sym-def");
  if (ds) { ds.innerHTML = Object.keys(state.sym ? state.sym.defs : { Default: 1 }).map(k => `<option>${esc(k)}</option>`).join(""); ds.value = state.sym ? state.sym.active : "Default"; }
}
function symPickLinks(v) {                                 // the pipes' Colour by select changed
  const d = symDef().links; d.color = v.startsWith("sym:") ? v.slice(4) : null;
  if (state.sym) enqueue(symSave);
}

/* ---- the Symbology dialog */
const symUi = { type: "links", cid: null };
let symSeq = 0;
const symNewId = () => "c" + Date.now().toString(36) + (symSeq++);
function symOpen(type) {
  if (!state.model) { toast("Open a project first."); return; }
  symUi.type = type || symUi.type; const d = symDef()[symUi.type];
  symUi.cid = d.color || (d.codings[0] && d.codings[0].id) || null;
  $("#dlg-sym").hidden = false; symRender();
}
function symFieldOptions(type, cur, withText = true) {
  const groups = {};
  for (const f of SYM_FIELDS[type]) if (withText || f[4] === "num") (groups[f[3]] = groups[f[3]] || []).push(f);
  return Object.entries(groups).map(([g, fs]) => `<optgroup label="${g}">${fs.map(f => `<option value="${f[0]}"${f[0] === cur ? " selected" : ""}>${esc(f[1])}${f[2] ? ` (${esc(f[2])})` : ""}</option>`).join("")}</optgroup>`).join("");
}
function symRender() {
  const type = symUi.type, def = symDef(), d = def[type], cd = d.codings.find(x => x.id === symUi.cid) || null;
  $$("#sym-tabs button").forEach(b => b.classList.toggle("on", b.dataset.type === type));
  $("#sym-def-name").textContent = state.sym.active;
  // colour codings list
  $("#sym-codings").innerHTML = d.codings.length ? d.codings.map(x => `<div class="sym-c${x.id === symUi.cid ? " on" : ""}" data-id="${esc(x.id)}" data-testid="sym-coding-${esc(x.name || x.field)}">` +
    `<label title="Show this colour coding on the map"><input type="radio" name="sym-use" data-act="use" ${d.color === x.id ? "checked" : ""}> ${esc(x.name || symField(type, x.field)[1])}</label>` +
    `<span class="muted">${esc(symField(type, x.field)[1])}</span><button class="mini" data-act="del" title="Delete this colour coding">&#215;</button></div>`).join("") +
    `<div class="sym-c" data-id=""><label><input type="radio" name="sym-use" data-act="use" ${d.color ? "" : "checked"}> none (${type === "links" ? "the Colour by choice" : type === "nodes" ? "colour by type" : "plain"})</label></div>`
    : `<p class="muted">No colour coding yet. New makes one; its colours show on the map once it is used.</p>`;
  // the selected coding's editor
  const ed = $("#sym-coding-ed");
  if (!cd) { ed.innerHTML = ""; }
  else {
    const f = symField(type, cd.field), text = f[4] === "text", r = symRange(cd, type), o = cd.init || {};
    ed.innerHTML =
      `<div class="sym-grid"><label>Name<input id="sym-name" type="text" value="${esc(cd.name || "")}" placeholder="${esc(f[1])}"></label>` +
      `<label>Field<select id="sym-field">${symFieldOptions(type, cd.field)}</select></label>` +
      `<label>Show as<select id="sym-mode"><option value="color"${cd.mode === "color" ? " selected" : ""}>colour</option><option value="size"${cd.mode === "size" ? " selected" : ""}>${type === "nodes" ? "symbol size" : "line width"}</option><option value="both"${cd.mode === "both" ? " selected" : ""}>colour and size</option></select></label>` +
      `<label>Applies to<select id="sym-scope"><option value="all"${cd.scope !== "ids" ? " selected" : ""}>all ${SYM_TYPES[type].toLowerCase()}</option><option value="ids"${cd.scope === "ids" ? " selected" : ""}>the ${(cd.ids || []).length} kept from a selection</option></select></label></div>` +
      `<div class="row"><button id="sym-take-sel" title="Keep the elements selected on the map as this coding's scope">Use the current selection</button>` +
      (text ? "" : `<span class="muted" id="sym-range">${r ? `range ${symRound(r[0])} to ${symRound(r[1])}${f[2] ? " " + esc(f[2]) : ""}` : "no values"}</span>`) + `</div>` +
      (text ? `<p class="muted">One class per value (up to 30).</p><div class="row"><button id="sym-init" class="primary">Initialize from the values</button></div>`
        : `<div class="sym-grid"><label>Minimum<input id="sym-min" type="number" step="any" value="${o.min ?? (r ? symRound(r[0]) : "")}"></label><label>Maximum<input id="sym-max" type="number" step="any" value="${o.max ?? (r ? symRoundUp(r[1]) : "")}"></label>` +
          `<label>Steps<input id="sym-steps" type="number" min="1" max="20" value="${o.steps ?? 5}"></label><label>Breaks<select id="sym-method"><option value="equal">equal widths</option><option value="quantile"${o.method === "quantile" ? " selected" : ""}>equal counts</option></select></label>` +
          `<label>Colours<select id="sym-ramp">${Object.keys(SYM_RAMPS).map(k => `<option${k === (o.ramp || "Blue to red") ? " selected" : ""}>${k}</option>`).join("")}</select></label>` +
          `<label class="chk"><input id="sym-reverse" type="checkbox"${o.reverse ? " checked" : ""}> reverse</label></div>` +
          `<div class="row"><button id="sym-calc" title="The smallest and largest value of the field">Calculate range</button><button id="sym-init" class="primary" title="Make the classes from the minimum, maximum and steps">Initialize</button></div>`) +
      `<table class="sym-tab"><thead><tr><th>${text ? "Value" : "Up to"}</th><th>Colour</th><th>Size</th><th></th></tr></thead><tbody>` +
      (text ? (cd.cats || []).map((x, i) => `<tr data-i="${i}"><td>${esc(x.value)}</td><td><input type="color" data-k="color" value="${x.color}"></td><td><input type="number" step="0.5" min="0" data-k="size" value="${x.size}"></td><td><button class="mini" data-act="row-del">&#215;</button></td></tr>`).join("")
        : (cd.breaks || []).map((b, i) => `<tr data-i="${i}"><td><input type="number" step="any" data-k="to" value="${b.to}"></td><td><input type="color" data-k="color" value="${b.color}"></td><td><input type="number" step="0.5" min="0" data-k="size" value="${b.size}"></td><td><button class="mini" data-act="row-del">&#215;</button></td></tr>`).join("") +
          `<tr data-i="above"><td class="muted">above the range</td><td><input type="color" data-k="color" value="${(cd.above || {}).color || "#7a0e3a"}"></td><td><input type="number" step="0.5" min="0" data-k="size" value="${(cd.above || {}).size ?? 9}"></td><td></td></tr>`) +
      `</tbody></table>` + (text ? "" : `<div class="row"><button id="sym-row-add">Add a class</button></div>`) +
      `<div class="row"><button id="sym-apply" class="primary" data-testid="sym-apply">Apply and show</button></div>`;
  }
  // labels
  const L = d.labels;
  $("#sym-labels").innerHTML =
    `<table class="sym-tab"><thead><tr><th>On</th><th>Field or text</th><th>Prefix</th><th>Suffix</th><th>Decimals</th><th title="On the same line as the label above">Same line</th><th></th></tr></thead><tbody>` +
    L.items.map((it, i) => `<tr data-i="${i}"><td><input type="checkbox" data-k="on"${it.on ? " checked" : ""}></td>` +
      (it.template != null ? `<td colspan="4"><input type="text" data-k="template" value="${esc(it.template)}" title="Free text: {field}, {field:2} for 2 decimals, {field:2:u} with units"></td>`
        : `<td><select data-k="field">${symFieldOptions(type, it.field)}</select></td><td><input type="text" data-k="prefix" value="${esc(it.prefix || "")}" title="%u is the field's unit"></td>` +
          `<td><input type="text" data-k="suffix" value="${esc(it.suffix || "")}" title="%u is the field's unit"></td><td><input type="number" min="0" max="6" data-k="dec" value="${it.dec ?? ""}"></td>`) +
      `<td><input type="checkbox" data-k="same"${it.same ? " checked" : ""}></td><td><button class="mini" data-act="lab-del">&#215;</button></td></tr>`).join("") +
    `</tbody></table>` +
    `<div class="row"><button id="sym-lab-add">Add a field</button><button id="sym-lab-free" title="Free text with fields in braces, e.g. {id} L={length_m:1} m">Add free text</button>` +
    `<label>Text size<input id="sym-lab-size" type="number" min="6" max="30" step="0.5" value="${L.size}"></label>` +
    `<label>Shown from zoom<input id="sym-lab-zoom" type="number" min="0" max="22" step="0.5" value="${L.minzoom}"></label>` +
    `<label title="Draw every label, even where labels overlap; off hides those that would overlap"><input id="sym-lab-overlap" type="checkbox"${(L.overlap ?? type === "links") ? " checked" : ""}> Overlap</label></div>` +
    `<div class="row"><button id="sym-lab-apply" class="primary" data-testid="sym-lab-apply">Apply labels</button><span class="muted">Example: <span id="sym-lab-ex">${esc(symExample(type))}</span></span></div>`;
  tag($("#dlg-sym"));
}
function symExample(type) {
  const m = state.model, T = type === "links" ? m.linkFeat : type === "nodes" ? m.nodeFeat : m.catchFeat;
  const f = T.find(x => x.properties.kind !== "pump") || T[0]; return f ? (symLabel(type, f, symDef()[type].labels, symContext()) || "(no label)").replace(/\n/g, " / ") : "-";
}
/* read the editor back into the coding (classes, options) */
function symReadCoding(cd) {
  const type = symUi.type, g = id => $("#" + id);
  if (g("sym-name")) cd.name = g("sym-name").value.trim();
  cd.mode = g("sym-mode").value; cd.scope = g("sym-scope").value;
  if (g("sym-min")) cd.init = { min: g("sym-min").value === "" ? null : +g("sym-min").value, max: g("sym-max").value === "" ? null : +g("sym-max").value, steps: +g("sym-steps").value || 5, method: g("sym-method").value, ramp: g("sym-ramp").value, reverse: g("sym-reverse").checked };
  for (const tr of $$("#sym-coding-ed tbody tr")) {
    const i = tr.dataset.i, val = k => { const e = tr.querySelector(`[data-k=${k}]`); return e ? e.value : null; };
    if (i === "above") { cd.above = { color: val("color"), size: +val("size") }; continue; }
    if (cd.cats && cd.cats.length) Object.assign(cd.cats[+i], { color: val("color"), size: +val("size") });
    else Object.assign(cd.breaks[+i], { to: +val("to"), color: val("color"), size: +val("size") });
  }
  if (cd.breaks) cd.breaks.sort((a, b) => a.to - b.to);
  return cd;
}
function symReadLabels() {
  const L = symDef()[symUi.type].labels;
  $$("#sym-labels tbody tr").forEach((tr, i) => {
    const it = L.items[i], v = k => tr.querySelector(`[data-k=${k}]`);
    it.on = v("on").checked; it.same = v("same").checked;
    if (it.template != null) it.template = v("template").value;
    else { it.field = v("field").value; it.prefix = v("prefix").value; it.suffix = v("suffix").value; it.dec = v("dec").value === "" ? null : +v("dec").value; }
  });
  L.size = +$("#sym-lab-size").value || L.size; L.minzoom = +$("#sym-lab-zoom").value; L.overlap = $("#sym-lab-overlap").checked;
  return L;
}
function wireSymbology() {
  const dlg = $("#dlg-sym");
  $("#sym-edit").onclick = () => symOpen("links");
  $("#sym-close").onclick = () => { dlg.hidden = true; };
  $("#sym-tabs").onclick = e => { const b = e.target.closest("button[data-type]"); if (!b) return; symUi.type = b.dataset.type; const d = symDef()[symUi.type]; symUi.cid = d.color || (d.codings[0] && d.codings[0].id) || null; symRender(); };
  $("#sym-new").onclick = () => {
    const type = symUi.type, d = symDef()[type], field = type === "links" ? "v_ms" : type === "nodes" ? "depth" : "imperv_pc";
    const cd = symInitialize({ id: symNewId(), name: "", field, mode: "color", scope: "all", ids: [] }, type, {});
    d.codings.push(cd); symUi.cid = cd.id; symRender();
  };
  $("#sym-codings").onclick = e => {
    const row = e.target.closest(".sym-c"); if (!row) return; const type = symUi.type, d = symDef()[type], id = row.dataset.id, act = e.target.dataset.act;
    if (act === "del") { d.codings = d.codings.filter(x => x.id !== id); if (d.color === id) d.color = null; if (symUi.cid === id) symUi.cid = null; symRender(); symRefresh(true); return; }
    if (act === "use") { d.color = id || null; if (type === "links") state.colorBy = id ? "sym:" + id : "v_ms"; symRefresh(true); }
    if (id) { symUi.cid = id; symRender(); }
  };
  $("#sym-coding-ed").addEventListener("change", e => {
    const cd = symDef()[symUi.type].codings.find(x => x.id === symUi.cid); if (!cd) return;
    if (e.target.id === "sym-field") { cd.field = e.target.value; cd.init = {}; symInitialize(cd, symUi.type, {}); symRender(); }
  });
  $("#sym-coding-ed").addEventListener("click", e => {
    const type = symUi.type, d = symDef()[type], cd = d.codings.find(x => x.id === symUi.cid); if (!cd) return;
    const id = e.target.id, act = e.target.dataset.act;
    if (id === "sym-calc") { const r = symRange(cd, type); if (r) { $("#sym-min").value = symRound(r[0]); $("#sym-max").value = symRoundUp(r[1]); } else toast("This field has no values here."); }
    else if (id === "sym-init") { symReadCoding(cd); symInitialize(cd, type, cd.init || {}); symRender(); }
    else if (id === "sym-row-add") { symReadCoding(cd); const last = cd.breaks[cd.breaks.length - 1]; cd.breaks.push({ to: last ? symRound(last.to * 1.5 || 1) : 1, color: "#888888", size: 4 }); symRender(); }
    else if (act === "row-del") { symReadCoding(cd); const i = +e.target.closest("tr").dataset.i; if (cd.cats && cd.cats.length) cd.cats.splice(i, 1); else cd.breaks.splice(i, 1); symRender(); }
    else if (id === "sym-take-sel") {
      if (state.sel.table !== SYM_TABLE[type] || !state.sel.ids.length) { toast(`Select some ${SYM_TYPES[type].toLowerCase()} on the map first.`); return; }
      symReadCoding(cd); cd.ids = state.sel.ids.slice(); cd.scope = "ids"; symRender();
    }
    else if (id === "sym-apply") { symReadCoding(cd); d.color = cd.id; if (type === "links") state.colorBy = "sym:" + cd.id; symRender(); symRefresh(true); }
  });
  $("#sym-labels").addEventListener("click", e => {
    const L = symDef()[symUi.type].labels, id = e.target.id;
    if (id === "sym-lab-add") { symReadLabels(); L.items.push({ on: true, field: "id" }); symRender(); }
    else if (id === "sym-lab-free") { symReadLabels(); L.items.push({ on: true, template: symUi.type === "links" ? "{id} L={length_m:1:u}" : "{id}" }); symRender(); }
    else if (e.target.dataset.act === "lab-del") { symReadLabels(); L.items.splice(+e.target.closest("tr").dataset.i, 1); symRender(); }
    else if (id === "sym-lab-apply") { symReadLabels(); symRefresh(true); symRender(); }
  });
  // named definitions
  $("#sym-def").onchange = e => { state.sym.active = e.target.value; symRefresh(true); if (!dlg.hidden) symRender(); };
  $("#sym-def-new").onclick = () => enqueue(async () => {
    const n = await askText("New symbology", "Name", ""); if (!n) return;
    if (state.sym.defs[n]) { toast("That name is taken."); return; }
    state.sym.defs[n] = JSON.parse(JSON.stringify(symDef())); state.sym.active = n; symRefresh(true); symRender();
  });
  $("#sym-def-rename").onclick = () => enqueue(async () => {
    const old = state.sym.active, n = await askText("Rename the symbology", "Name", old); if (!n || n === old) return;
    if (state.sym.defs[n]) { toast("That name is taken."); return; }
    state.sym.defs[n] = state.sym.defs[old]; delete state.sym.defs[old]; state.sym.active = n; symRefresh(true); symRender();
  });
  $("#sym-def-del").onclick = () => enqueue(async () => {
    if (Object.keys(state.sym.defs).length < 2) { toast("The last symbology cannot be deleted."); return; }
    if (!(await askText(`Delete "${state.sym.active}"?`, "", "", true))) return;
    delete state.sym.defs[state.sym.active]; state.sym.active = Object.keys(state.sym.defs)[0]; symRefresh(true); symRender();
  });
  // Display card selects for structures and catchments
  for (const [type, sel] of [["nodes", "#node-color-by"], ["catchments", "#catch-color-by"]])
    $(sel).onchange = e => { symDef()[type].color = e.target.value || null; symRefresh(true); };
  $("#legend").addEventListener("click", e => { const r = e.target.closest(".sym-row"); if (r) symSelectClass(r.dataset.type, +r.dataset.i); });
}
