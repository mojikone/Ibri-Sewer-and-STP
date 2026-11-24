/* W19 v7 (2026-11-24): drawing appears at the click, and every element kind SewerGEMS draws has its place: the ribbon,
   the layout tool's right-click, the symbology tabs, the map's colours and symbols, Properties.

   The engineer, 2026-11-24: "when I use elements to draw like manhole or the layout tool, it takes 1 or 2 seconds to
   appear on screen. Can it become realtime?" and "when you add items to right click (when drawing using layout) or
   symbology tabs, add all items. Do not leave the work half done." */

/* ------------------------------------------------------------------ the element kinds, in one place
   kind: [table, label, plural, id prefix, colour, ribbon tool id (a node tool places it; a link tool draws it)] */
const KINDS = {
  manhole: ["nodes", "Manhole", "Manholes", "MH-", "#8a94a0", "manhole"],
  catch_basin: ["nodes", "Catch basin", "Catch basins", "CB-", "#2e8b57", "catchbasin"],
  outfall: ["nodes", "Outfall", "Outfalls", "O-", "#123e7c", "outfall"],
  headwall: ["nodes", "Headwall", "Headwalls", "HW-", "#1f5f8b", "headwall"],
  transition: ["nodes", "Transition", "Transitions", "TR-", "#a0784f", "transition"],
  cross_section: ["nodes", "Cross section", "Cross sections", "CS-", "#4f8fa0", "xsection"],
  wetwell: ["nodes", "Wet well", "Wet wells", "WW-", "#7b3fa0", "wetwell"],
  storage: ["nodes", "Pond (storage)", "Ponds and storage", "PO-", "#1b9e77", "pond"],
  junction: ["nodes", "Junction", "Junctions", "JN-", "#c9a227", "junction"],
  pressure_junction: ["nodes", "Pressure junction", "Pressure junctions", "J-", "#3b0a45", "pjunction"],
  air_valve: ["nodes", "Air valve", "Air valves", "AV-", "#c0392b", "airvalve"],
  property_connection: ["nodes", "Property connection", "Property connections", "PC-", "#b5651d", "propconn"],
  tap: ["nodes", "Tap", "Taps", "TAP-", "#6b6b6b", "tap"],
  conduit: ["links", "Conduit", "Conduits", "P-", "#2f6fd0", "pipe"],
  channel: ["links", "Channel", "Channels", "CH-", "#1b8a9a", "channel"],
  gutter: ["links", "Gutter", "Gutters", "GT-", "#7fa650", "gutter"],
  lateral: ["links", "Lateral", "Laterals", "LT-", "#b5651d", "lateral"],
  pressure_pipe: ["links", "Pressure pipe", "Pressure pipes", "FM-", "#3b0a45", "ppipe"],
  pump: ["links", "Pump", "Pumps", "PMP-", "#7b3fa0", "pump"],
  orifice: ["links", "Orifice", "Orifices", "OR-", "#0e7c86", "orifice"],
  weir: ["links", "Weir", "Weirs", "WR-", "#0e7c86", "weir"],
};
const KIND_NAMES = Object.fromEntries(Object.entries(KINDS).map(([k, v]) => [k, v[1].toLowerCase().replace(" (storage)", "")]));
window.KIND_NAMES = KIND_NAMES;
const kindsOf = table => Object.keys(KINDS).filter(k => KINDS[k][0] === table);

/* ------------------------------------------------------------------ the left dock follows the map's height, as Properties does
   (the engineer, 2026-11-24: "when I expand the bottom pane, the symbology does not get smaller"): its top and bottom
   track the map area whenever that changes size (the tables' splitter, the ribbon folding, the window) */
(function dockFollowsMap() {
  const wrap = document.getElementById("map-wrap"); if (!wrap || !window.ResizeObserver) return;
  const fit = () => {
    const r = wrap.getBoundingClientRect(), s = document.body.style;
    const top = r.top + "px", bot = Math.max(0, innerHeight - r.bottom) + "px";
    if (s.getPropertyValue("--dock-top") !== top) s.setProperty("--dock-top", top);
    if (s.getPropertyValue("--dock-bottom") !== bot) s.setProperty("--dock-bottom", bot);
  };
  new ResizeObserver(fit).observe(wrap); addEventListener("resize", fit);
})();

/* ------------------------------------------------------------------ drawing appears at the click
   Each click that places a structure or draws a link shows it at once, as a ghost, while the edit travels to the server
   and back (over a tunnel that is a few hundred milliseconds); the real element replaces it when the answer arrives.
   Clicks queue in order, so a quick run of layout clicks chains its ghosts from one to the next. */
const GHOST = { list: [], seq: 0 };
function ghostLayers() {
  if (!map || !map.getSource) return false; if (map.getSource("ghost")) return true;
  if (!map.isStyleLoaded || !map.getLayer("nodes")) return false;
  map.addSource("ghost", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addLayer({ id: "ghost-line", type: "line", source: "ghost", filter: ["==", ["geometry-type"], "LineString"], layout: { "line-cap": "round" },
    paint: { "line-color": ["coalesce", ["get", "c"], "#2f6fd0"], "line-width": 3, "line-opacity": 0.85 } });
  map.addLayer({ id: "ghost-pt", type: "circle", source: "ghost", filter: ["==", ["geometry-type"], "Point"],
    paint: { "circle-radius": 6, "circle-color": ["coalesce", ["get", "c"], "#8a94a0"], "circle-stroke-color": "#fff", "circle-stroke-width": 2, "circle-opacity": 0.9 } });
  return true;
}
function ghostDraw() {
  if (!ghostLayers()) return;
  map.getSource("ghost").setData({ type: "FeatureCollection", features: GHOST.list.flatMap(g => g.feats) });
}
const LINK_TOOLS = { pipe: "conduit", ppipe: "pressure_pipe", pump: "pump", orifice: "orifice", weir: "weir", channel: "channel", gutter: "gutter", lateral: "lateral" };
function ghostAt(ll) {
  if (!state.pid || !state.model || !map) return null;
  const t = state.tool, pt = map.project(ll), [tn, tl] = pickTol();
  const nn = nearestNode(pt, tn), nl = nn ? null : nearestLink(pt, tl);
  const here = [ll.lng, ll.lat], feats = [], col = k => (KINDS[k] || [])[4];
  const at = id => { const f = state.model.nodes.get(id); return f ? f.geometry.coordinates : null; };
  const lastEnd = () => { for (let i = GHOST.list.length - 1; i >= 0; i--) if (GHOST.list[i].end) return GHOST.list[i].end; return null; };
  const pointF = (c, k) => ({ type: "Feature", properties: { c: col(k) }, geometry: { type: "Point", coordinates: c } });
  const lineF = (cs, k) => ({ type: "Feature", properties: { c: col(k) }, geometry: { type: "LineString", coordinates: cs } });
  let end = null;
  if (ADD_NODE[t]) { if (!nn && !nl) feats.push(pointF(here, ADD_NODE[t][0])); }
  else if (t === "layout" && !layout.bend) {
    const from = lastEnd() || (layout.last && at(layout.last)), to = nn ? at(nn.id) : here;
    if (from && to) feats.push(lineF([from, ...(layout.via || []), to], layout.link || "conduit"));
    if (!nn && !nl) feats.push(pointF(here, layout.node));
    end = to;
  } else if (LINK_TOOLS[t] && state.pipeStart) {
    const from = at(state.pipeStart), to = nn ? at(nn.id) : here;
    if (from && to && (!nn || nn.id !== state.pipeStart)) feats.push(lineF([from, to], LINK_TOOLS[t]));
    if (!nn && !nl) feats.push(pointF(here, t === "pipe" || t === "channel" || t === "lateral" ? "manhole" : t === "gutter" ? "catch_basin" : "pressure_junction"));
  }
  if (!feats.length) return null;
  const g = { id: ++GHOST.seq, feats, end }; GHOST.list.push(g); ghostDraw(); return g;
}
function ghostDone(g) { const n = GHOST.list.length; GHOST.list = GHOST.list.filter(x => x !== g); if (GHOST.list.length !== n) ghostDraw(); }
window.ed.ghosts = () => GHOST.list.length;

/* ------------------------------------------------------------------ the tools for every kind */
Object.assign(ADD_NODE, { catchbasin: ["catch_basin", "CB-"], headwall: ["headwall", "HW-"], transition: ["transition", "TR-"], xsection: ["cross_section", "CS-"],
  pond: ["storage", "PO-"], airvalve: ["air_valve", "AV-"], propconn: ["property_connection", "PC-"] });
Object.assign(HINTS, {
  catchbasin: "Catch basin: click the map; click a pipe to split it, a structure to morph it. Its inlet (capture, grate, curb, gutter) is in Properties.",
  headwall: "Headwall: a culvert's end; click the map, a pipe or a structure. Its boundary condition is in Properties.",
  transition: "Transition: a pipe-to-pipe joint with no structure; click the map or a pipe.",
  xsection: "Cross section: a channel's node; click the map or a channel.",
  pond: "Pond (storage): click the map; its plan area or depth-area table is in Properties.",
  airvalve: "Air valve: click the map or a force main.",
  propconn: "Property connection: a property's sanitary load (Properties > Loads); join it to the network with a lateral.",
  tap: "Tap: click the conduit where a lateral joins it (the conduit is not split; the lateral's flow enters it).",
  channel: "Channel: click the start, then the end (an empty spot makes a cross section); give it its open section in Properties.",
  gutter: "Gutter: from one catch basin to the next (an empty spot makes a catch basin): the first inlet's bypass runs down it.",
  lateral: "Lateral: from a property connection (an empty spot makes one) to a manhole, or click a conduit to end on a tap there.",
});

/* ------------------------------------------------------------------ the layout tool's right-click: every structure, every link */
LAY_KINDS.splice(0, LAY_KINDS.length, ...["manhole", "catch_basin", "outfall", "headwall", "transition", "cross_section", "wetwell", "storage", "pressure_junction", "air_valve", "property_connection"].map(k => [k, KINDS[k][1]]));
const LAY_LINKS = [["conduit", "Conduit"], ["channel", "Channel"], ["gutter", "Gutter"], ["lateral", "Lateral"], ["pressure_pipe", "Pressure pipe"]];
function setLayoutLink(k) {
  const s = $("#layout-link"); if (s) { s.value = k; s.dispatchEvent(new Event("change")); } else layout.link = k;
  $("#hint").textContent = `Next link: ${k.replace("_", " ")}.`; if (typeof layoutPreview === "function") layoutPreview();
}
function layoutMenu(x, y) {
  const cur = layout.bend ? "bend" : layout.node, lk = layout.link || "conduit";
  ctxOpen(x, y, [{ head: "Layout" },
    { label: "Done: end the run", keys: "Esc", key: "lay-done", disabled: !layout.last, run: () => { layout.last = null; layout.via = []; layout.bend = false; layoutPreview(); $("#hint").textContent = HINTS.layout; } },
    ...(layout.via.length ? [{ label: "Remove the last bend", key: "lay-unbend", run: () => { layout.via.pop(); layoutPreview(); } }] : []),
    "-", { head: "Next point" },
    ...LAY_KINDS.map(([k, l]) => ({ label: (cur === k ? "● " : "○ ") + l, key: "lay-next-" + k, run: () => setLayoutNext(k) })),
    { label: (cur === "bend" ? "● " : "○ ") + "Bend (a vertex of the link, no structure)", key: "lay-next-bend", run: () => setLayoutNext("bend") },
    "-", { head: "Next link" },
    ...LAY_LINKS.map(([k, l]) => ({ label: (lk === k ? "● " : "○ ") + l, key: "lay-link-" + k, run: () => setLayoutLink(k) })),
    { label: "Pump (from a wet well): use the Pump tool", key: "lay-link-pump", run: () => { layout.last = null; setTool("pump"); } }]);
}

/* ------------------------------------------------------------------ the map: each kind's colour and symbol */
function kindIcon(kind) {
  const c = document.createElement("canvas"); c.width = c.height = 32; const g = c.getContext("2d"), col = KINDS[kind][4];
  g.lineWidth = 3; g.strokeStyle = col; g.fillStyle = "#fff";
  const sq = (x, y, w, h) => { g.beginPath(); g.rect(x, y, w, h); g.fill(); g.stroke(); };
  if (kind === "catch_basin") { sq(6, 6, 20, 20); g.lineWidth = 2; for (const x of [12, 16, 20]) { g.beginPath(); g.moveTo(x, 7); g.lineTo(x, 25); g.stroke(); } }
  else if (kind === "headwall") { g.fillStyle = col; g.fillRect(5, 8, 22, 8); g.fillRect(8, 16, 4, 10); g.fillRect(20, 16, 4, 10); }
  else if (kind === "transition") { g.beginPath(); g.moveTo(16, 5); g.lineTo(27, 16); g.lineTo(16, 27); g.lineTo(5, 16); g.closePath(); g.fill(); g.stroke(); }
  else if (kind === "cross_section") { g.beginPath(); g.moveTo(5, 9); g.lineTo(11, 24); g.lineTo(21, 24); g.lineTo(27, 9); g.stroke(); }
  else if (kind === "air_valve") { g.fillStyle = col; g.beginPath(); g.moveTo(16, 5); g.lineTo(28, 26); g.lineTo(4, 26); g.closePath(); g.fill(); }
  else if (kind === "property_connection") { g.beginPath(); g.moveTo(5, 16); g.lineTo(16, 6); g.lineTo(27, 16); g.lineTo(27, 27); g.lineTo(5, 27); g.closePath(); g.fill(); g.stroke(); }
  else if (kind === "tap") { g.beginPath(); g.arc(16, 16, 7, 0, 2 * Math.PI); g.fill(); g.stroke(); }
  else if (kind === "storage") { g.fillStyle = col; g.globalAlpha = 0.85; g.fillRect(4, 10, 24, 15); g.globalAlpha = 1; g.strokeStyle = "#fff"; g.lineWidth = 2; g.beginPath(); g.moveTo(6, 14); g.quadraticCurveTo(11, 10, 16, 14); g.quadraticCurveTo(21, 18, 26, 14); g.stroke(); }
  return g.getImageData(0, 0, 32, 32);
}
const ICON_KINDS = ["catch_basin", "headwall", "transition", "cross_section", "air_valve", "property_connection", "tap", "storage"];
(async function mapKinds() {
  await mapReady;
  const fl = ["==", ["coalesce", ["get", "_fl"], 0], 1];
  const kc = ["match", ["get", "kind"], ...Object.entries(KINDS).filter(([, v]) => v[0] === "nodes" && v[4]).flatMap(([k, v]) => [k, v[4]]), "#8a94a0"];
  map.setPaintProperty("nodes", "circle-color", ["case", fl, "#d7301f", ["has", "_c"], ["get", "_c"], kc]);
  for (const k of ICON_KINDS) if (!map.hasImage("k-" + k)) map.addImage("k-" + k, kindIcon(k), { pixelRatio: 2 });
  map.addLayer({ id: "nodes-icon", type: "symbol", source: "nodes", minzoom: 14.5, filter: ["in", ["get", "kind"], ["literal", ICON_KINDS]],
    layout: { "icon-image": ["concat", "k-", ["get", "kind"]], "icon-size": ["interpolate", ["linear"], ["zoom"], 14.5, 0.7, 17, 1, 19, 1.4], "icon-allow-overlap": true, "icon-ignore-placement": true } }, "nodes-label");
  const w = ["interpolate", ["linear"], ["zoom"], 12, 1.2, 16, 2.5, 19, 4];
  map.addLayer({ id: "links-gutter", type: "line", source: "links", filter: ["==", ["get", "kind"], "gutter"], layout: { "line-cap": "butt" },
    paint: { "line-color": KINDS.gutter[4], "line-width": w, "line-dasharray": [3, 2] } }, "links-arrow");
  map.addLayer({ id: "links-lateral", type: "line", source: "links", filter: ["==", ["get", "kind"], "lateral"],
    paint: { "line-color": KINDS.lateral[4], "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.8, 16, 1.6, 19, 3] } }, "links-arrow");
  map.addLayer({ id: "links-channel", type: "line", source: "links", filter: ["==", ["get", "kind"], "channel"],
    paint: { "line-color": "#bfe6ea", "line-width": ["interpolate", ["linear"], ["zoom"], 12, 0.6, 16, 1.2, 19, 2] } }, "links-arrow");
})();

/* ------------------------------------------------------------------ Properties: each kind's own fields (SewerGEMS's)
   The fields come from the server (model/kinds.py), grouped as SewerGEMS groups them; a catch basin shows only what its
   inlet type uses (a percent for percent capture, the grate's size for a grate, the gutter for a catalogue inlet...). */
const OPT_NAMES = { full_capture: "Full capture", percent_capture: "Percent capture", max_capacity: "Maximum capacity", rating_curve: "Inflow-capture curve", catalog: "Catalogue inlet (HEC-22)",
  on_grade: "On grade", in_sag: "In sag", grate: "Grate", curb: "Curb opening", combination: "Combination (grate and curb)", slot: "Slotted drain",
  p50: "P-50 mm", p50x100: "P-50 x 100 mm", p30: "P-30 mm", curved_vane: "Curved vane", tilt_bar_45: "45-degree tilt bar", tilt_bar_30: "30-degree tilt bar", reticuline: "Reticuline",
  vertical: "Vertical", inclined: "Inclined", horizontal: "Horizontal", conventional: "Conventional", v_shaped: "V-shaped", trapezoidal: "Trapezoidal (ditch)",
  circular: "Circular", box: "Box", free: "Free outfall", fixed: "Fixed tailwater", invert_to_center: "Invert to centre", invert_to_crown: "Invert to crown",
  from_start_inlet: "Derived from the start inlet" };
function kfShow(kind, k, P) {
  if (kind === "catch_basin") {
    const t = P.inlet_type || "full_capture", c = P.inlet_class, cat = t === "catalog", sh = P.gutter_shape || "conventional";
    if (k === "capture_pc") return t === "percent_capture";
    if (k === "q_max_ls") return t === "max_capacity";
    if (k === "rating") return t === "rating_curve";
    if (["location", "inlet_class", "clogging_pc", "road_cross_slope", "n_gutter", "gutter_shape", "max_gutter_depth_m", "max_spread_m"].includes(k)) return cat;
    if (k === "long_slope") return cat && (P.location || "on_grade") === "on_grade";
    if (["grate_type", "grate_length_m", "grate_width_m", "opening_ratio"].includes(k)) return cat && ["grate", "combination"].includes(c);
    if (["curb_length_m", "curb_height_m", "throat"].includes(k)) return cat && ["curb", "combination"].includes(c);
    if (["slot_length_m", "slot_width_m"].includes(k)) return cat && c === "slot";
    if (["gutter_cross_slope", "gutter_width_m"].includes(k)) return cat && sh === "conventional";
    if (k === "curb_cross_slope") return cat && sh === "v_shaped";
    if (["ditch_bottom_m", "side_slope_l", "side_slope_r"].includes(k)) return cat && sh === "trapezoidal";
  }
  if (kind === "catch_basin" || kind === "manhole") { if (k === "diameter_m") return (P.structure || "circular") === "circular"; if (["box_length_m", "box_width_m"].includes(k)) return P.structure === "box"; }
  if (kind === "headwall" && k === "tailwater_m") return P.boundary === "fixed";
  if (kind === "gutter" && ["road_cross_slope", "gutter_cross_slope", "gutter_width_m"].includes(k)) return !!P.gutter_shape && P.gutter_shape !== "from_start_inlet";
  return true;
}
function kfControl(f, v) {
  const id = `kf-${f.key}`, a = `id="${id}" data-kf="${f.key}" data-testid="${id}"`;
  if (f.type === "choice") return `<select ${a}>${v === undefined ? `<option value="" selected>(mixed)</option>` : ""}${f.options.map(o => `<option value="${o}"${o === v ? " selected" : ""}>${esc(OPT_NAMES[o] || o.replace(/_/g, " "))}</option>`).join("")}</select>`;
  if (f.type === "bool") return `<input type="checkbox" ${a}${v ? " checked" : ""}>`;
  if (f.type === "text") return `<input type="text" ${a} value="${v == null ? "" : esc(String(v))}"${f.key === "link" ? ` list="kf-links"` : ""}>`;
  if (f.type === "table") {
    const rows = (v || []).concat([["", ""]]);
    return `<table class="kf-tab" data-kf="${f.key}"><thead><tr><th>Inflow (L/s)</th><th>Captured (L/s)</th></tr></thead><tbody>${rows.map(r => `<tr><td><input type="number" step="any" value="${r[0]}"></td><td><input type="number" step="any" value="${r[1]}"></td></tr>`).join("")}</tbody></table>` +
      `<button id="kf-${f.key}-add" data-testid="kf-${f.key}-add" class="small">+ Add row</button>`;
  }
  return `<input type="number" step="any" min="0" ${a} value="${v == null ? "" : +(+v).toFixed(6)}">`;
}
function kindFieldsBlock() {
  const host = $("#prop-grid"); if (!host || !state.info || !state.info.kind_fields || !state.model) return;
  const fs = selFeatures(), table = state.sel.table, old = $("#kind-fields");
  if (!fs.length || !["nodes", "links"].includes(table)) { if (old) old.remove(); return; }
  const kind = fs[0].properties.kind, spec = state.info.kind_fields[kind];
  if (!spec || !fs.every(f => f.properties.kind === kind)) { if (old) old.remove(); return; }
  const sig = [table, state.sel.ids.join(","), JSON.stringify(fs.map(f => f.properties.props || {})), JSON.stringify(state.inletRows || {})].join("|");
  const ae = document.activeElement, typing = old && old.contains(ae) && ae.tagName === "INPUT" && /^(text|number)$/.test(ae.type);   // a choice re-draws at once
  if (old && old.parentElement === host && (old.dataset.sig === sig || typing)) return;
  const same = k => { const v0 = (fs[0].properties.props || {})[k]; return fs.every(f => JSON.stringify((f.properties.props || {})[k]) === JSON.stringify(v0)) ? v0 : undefined; };
  const P = Object.fromEntries(spec.map(f => [f.key, same(f.key)])), groups = {};
  for (const f of spec) if (kfShow(kind, f.key, P)) (groups[f.group] = groups[f.group] || []).push(f);
  let h = `<h5>${esc(KINDS[kind] ? KINDS[kind][1] : kind)}</h5>`;
  for (const [g, fl] of Object.entries(groups)) {
    h += `<details class="kf-g" open data-testid="kf-group-${esc(g)}"><summary>${esc(g)}</summary>`;
    for (const f of fl) h += f.type === "table" ? `<div class="kf-t"><label>${esc(f.label)}</label>${kfControl(f, P[f.key])}</div>`
      : `<div class="pr"><label for="kf-${f.key}">${esc(f.label)}</label>${kfControl(f, P[f.key])}<span class="u">${esc(f.unit || "")}</span></div>`;
    h += `</details>`;
  }
  const R = kind === "catch_basin" && fs.length === 1 && state.inletRows && state.inletRows[fs[0].id];
  if (R) h += `<details class="kf-g" open data-testid="kf-results"><summary>Last rational run</summary><p class="small">Surface flow ${num(R.q_gutter_ls, 1)} L/s (local ${num(R.q_local_ls, 1)}, from upstream ${num(R.q_carry_in_ls, 1)});
    captured ${num(R.q_captured_ls, 1)} L/s${R.efficiency != null ? ` (${num(100 * R.efficiency, 0)} %)` : ""}; bypass ${num(R.q_bypass_ls, 1)} L/s${R.bypass_to ? ` to ${esc(R.bypass_to)}` : ""}${R.spread_m != null ? `; spread ${num(R.spread_m, 2)} m, depth ${num(R.depth_m, 3)} m` : ""}${R.spread_over ? ` <b class="bad">over the maximum spread</b>` : ""}${R.depth_over ? ` <b class="bad">over the maximum depth</b>` : ""}</p></details>`;
  if (kind === "tap") h += `<datalist id="kf-links">${state.model.linkFeat.filter(f => ["conduit", "channel"].includes(f.properties.kind)).slice(0, 3000).map(f => `<option value="${esc(String(f.id))}">`).join("")}</datalist>`;
  const box = old || document.createElement("div"); box.id = "kind-fields"; box.dataset.testid = "kind-fields"; box.innerHTML = h; box.dataset.sig = sig;
  if (box.parentElement !== host) host.appendChild(box);
  const ids = state.sel.ids.slice(), send = values => enqueue(() => exec({ op: "set_props", table, ids, values }));
  box.onchange = e => {
    const el = e.target, tab = el.closest(".kf-tab");
    if (tab) {
      const rows = [...tab.querySelectorAll("tbody tr")].map(tr => [...tr.querySelectorAll("input")].map(i => i.value.trim())).filter(r => r[0] !== "" && r[1] !== "").map(r => [Number(r[0]), Number(r[1])]);
      send({ [tab.dataset.kf]: rows.length ? rows : null }); return;
    }
    const k = el.dataset.kf; if (!k) return;
    const f = spec.find(x => x.key === k); let v;
    if (f.type === "bool") v = el.checked; else if (f.type === "choice" || f.type === "text") v = el.value === "" ? null : el.value;
    else v = el.value === "" ? null : Number(el.value);
    send({ [k]: v });
  };
  box.onclick = e => {
    const b = e.target.closest("button[id$='-add']"); if (!b) return;
    const tb = b.previousElementSibling.querySelector("tbody"); tb.insertAdjacentHTML("beforeend", `<tr><td><input type="number" step="any"></td><td><input type="number" step="any"></td></tr>`);
  };
}
(function wireKindFields() {
  const rp = renderProps;
  renderProps = function () { const r = rp.apply(this, arguments); try { kindFieldsBlock(); } catch (e) { console.warn(e); } return r; };
})();

/* ------------------------------------------------------------------ the rational run: the inlets first (capture, bypass, spread) */
runRational = async function () {
  if (!state.pid) return;
  const r = await jget(`${base()}/rational`);
  state.inletRows = Object.fromEntries((r.inlets || []).map(x => [x.id, x]));
  const inl = (r.inlets || []).map(x => ({ ...x, q_rational_ls: x.q_captured_ls, efficiency_pc: x.efficiency == null ? null : 100 * x.efficiency }));
  state.toolout = { tool: { label: `Rational method (steady storm): Q = C i A / 360${inl.length ? `; ${inl.length} inlets by HEC-22, then the pipes` : ""}` }, rows: [...inl, ...r.rows],
    cols: inl.length ? ["id", "q_gutter_ls", "q_captured_ls", "efficiency_pc", "q_bypass_ls", "bypass_to", "spread_m", "depth_m", "q_rational_ls", "ca_ha", "tc_min", "i_mm_h", "v_ms", "d_over_D", "surcharged"]
      : ["id", "q_rational_ls", "ca_ha", "tc_min", "i_mm_h", "v_ms", "d_over_D", "surcharged"], report: r.report };
  showTab("toolout"); renderAll();
};
