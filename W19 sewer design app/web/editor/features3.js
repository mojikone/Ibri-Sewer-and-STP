"use strict";
/* W19 v3 (2026-11-23): unit loads and patterns, dry weather on SWMM, user notifications, selection sets, queries,
   FlexTable columns and statistics, SewerGEMS's manager shortcuts. Loaded after features.js; uses editor.js. */

/* ------------------------------------------------------------------ unit loads (library) and a node's unit-load rows */
const UL_TYPES = { population: "Population (per person)", area: "Area (per ha)", discharge: "Discharge (per unit)", count: "Count (per item)" };
const unitLoads = () => ((state.model && state.model.settings.libraries) || {}).unit_loads || [];
function openUnitLoads() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-units-lib", "Unit sanitary loads", true), b = d.querySelector(".body");
  const draft = JSON.parse(JSON.stringify(unitLoads()));
  const render = () => {
    b.innerHTML = `<p class="muted">A unit load is a flow per unit (a person, a hectare, a school...). Structures take rows of unit load and count (Properties); the flow is peaked with the load upstream. Population methods peak on people: a population type counts its units, the others their population equivalent.</p>
      <table class="lib-tab"><thead><tr><th>Name</th><th>Type</th><th>Load per unit (L/d)</th><th>Unit</th><th>People per unit</th><th></th></tr></thead><tbody>` +
      draft.map((u, i) => `<tr data-i="${i}"><td><input data-f="name" value="${esc(u.name)}"></td><td><select data-f="type">${Object.entries(UL_TYPES).map(([k, l]) => `<option value="${k}"${k === u.type ? " selected" : ""}>${l}</option>`).join("")}</select></td>` +
        `<td><input type="number" step="any" min="0" data-f="rate" value="${+(u.rate_m3d * 1000).toFixed(4)}"></td><td><input data-f="unit" value="${esc(u.unit || "")}" style="width:80px"></td>` +
        `<td>${u.type === "population" ? `<span class="muted">1</span>` : `<input type="number" step="any" min="0" data-f="pe" value="${u.pe ?? ""}" style="width:70px">`}</td><td><button data-a="del">&times;</button></td></tr>`).join("") +
      `</tbody></table><div class="row"><button data-a="add" data-testid="ul-add">Add a unit load</button></div>`;
    tag(b);
  };
  const collect = () => { for (const tr of $$("tr[data-i]", b)) { const u = draft[+tr.dataset.i]; for (const el of $$("[data-f]", tr)) { const f = el.dataset.f; if (f === "rate") u.rate_m3d = Number(el.value || 0) / 1000; else if (f === "pe") u.pe = el.value === "" ? null : Number(el.value); else u[f] = el.value.trim(); } } };
  render(); d.hidden = false;
  b.onchange = e => { if (e.target.dataset.f === "type") { collect(); render(); } };
  d.onclick = e => {
    const t = e.target.closest("button"); if (!t) return; const a = t.dataset.a || t.dataset.act; if (!a) return;
    if (a === "close") { d.hidden = true; return; }
    collect();
    if (a === "add") { draft.push({ name: `Unit ${draft.length + 1}`, type: "population", rate_m3d: 0.2, unit: "person" }); render(); return; }
    if (a === "del") { draft.splice(+t.closest("tr").dataset.i, 1); render(); return; }
    if (a === "ok") {
      const names = draft.map(u => u.name); if (new Set(names).size !== names.length || names.some(n => !n)) { toast("Each unit load needs its own name."); return; }
      enqueue(async () => { await exec({ op: "set_setting", path: "libraries.unit_loads", value: draft }); d.hidden = true; toast(`${draft.length} unit load${draft.length === 1 ? "" : "s"} saved with the project.`, "info"); gridSig = ""; renderProps(); });
    }
  };
}
function unitRowsBlock(table, fs) {
  if (table !== "nodes") return "";
  const ls = state.model.settings.design_load, R = ((state.model.unit_rows || {})[ls] || {}), lib = unitLoads();
  const rows0 = JSON.stringify(R[fs[0].id] || []), same = fs.every(f => JSON.stringify(R[f.id] || []) === rows0), rows = same ? JSON.parse(rows0) : [];
  const total = rows.reduce((s, [n, c]) => { const u = lib.find(x => x.name === n); return s + (u ? c * u.rate_m3d : 0); }, 0);
  return `<h5>Unit loads <span class="muted small">(${esc(ls)}, peaked)</span></h5>` + (!lib.length ? `<p class="muted small">No unit loads in the library yet: Components &gt; Unit loads.</p>` :
    `<div id="ur-rows">${!same ? `<p class="muted small">Different rows on the selected structures; rows set here replace them on all.</p>` : ""}` +
    rows.map(([n, c], i) => `<div class="pr ur" data-i="${i}"><select data-k="u">${lib.map(u => `<option${u.name === n ? " selected" : ""}>${esc(u.name)}</option>`).join("")}</select><input type="number" step="any" min="0" data-k="c" value="${c}"><button class="mini" data-k="x" title="Remove">&times;</button></div>`).join("") +
    `</div><div class="row"><button id="ur-add" data-testid="ur-add">Add row</button><button id="ur-apply" data-testid="ur-apply">Apply rows</button><span class="muted small">${same && rows.length ? `${num(toShow("load", total), 3)} ${unitOf("load").u} on each` : ""}</span></div>`);
}
function wireUnitRows(host) {
  const box = $("#ur-rows", host); if (!box) return;
  const lib = unitLoads();
  $("#ur-add", host).onclick = () => { box.insertAdjacentHTML("beforeend", `<div class="pr ur"><select data-k="u">${lib.map(u => `<option>${esc(u.name)}</option>`).join("")}</select><input type="number" step="any" min="0" data-k="c" value="1"><button class="mini" data-k="x">&times;</button></div>`); };
  box.onclick = e => { if (e.target.dataset.k === "x") e.target.closest(".ur").remove(); };
  $("#ur-apply", host).onclick = () => {
    const rows = $$(".ur", box).map(r => [$("[data-k=u]", r).value, Number($("[data-k=c]", r).value || 0)]).filter(r => r[1] > 0);
    const ids = state.sel.ids.slice(), set = state.model.settings.design_load;
    enqueue(async () => { await exec({ op: "set_unit_rows", set, ids, rows }); toast(`Unit-load rows set on ${ids.length} structure${ids.length > 1 ? "s" : ""}.`, "info"); });
  };
}

/* ------------------------------------------------------------------ patterns and the dry-weather run on SWMM */
const patterns = () => ((state.model && state.model.settings.libraries) || {}).patterns || [];
function openPatterns() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-patterns", "Patterns and dry weather", true), b = d.querySelector(".body");
  const draft = JSON.parse(JSON.stringify(patterns())); let cur = 0;
  const S = state.model.settings, dw = Object.assign({ on: false, load_set: null, pattern: null, hours: 48 }, S.swmm_dwf || {});
  const sets = Object.keys(state.model.loads || {});
  const render = () => {
    const x = draft[cur];
    b.innerHTML = `<div class="pd-wrap"><div class="pd-list"><div class="list">${draft.map((p, i) => `<button data-i="${i}" class="${i === cur ? "on" : ""}">${esc(p.name)}</button>`).join("") || `<span class="muted">No patterns yet.</span>`}</div>
      <div class="row"><button data-a="add" data-testid="pat-add">Add</button><button data-a="del"${x ? "" : " disabled"}>Delete</button></div>
      <fieldset><legend>Dry weather on SWMM</legend><label class="rad"><input type="checkbox" data-w="on"${dw.on ? " checked" : ""}> Add the dry-weather flow to SWMM runs</label>
      <label>Load set<select data-w="load_set">${sets.map(s => `<option${s === (dw.load_set || S.design_load) ? " selected" : ""}>${esc(s)}</option>`).join("")}</select></label>
      <label>Pattern<select data-w="pattern"><option value="">(none: constant)</option>${draft.map(p => `<option${p.name === dw.pattern ? " selected" : ""}>${esc(p.name)}</option>`).join("")}</select></label>
      <label>Duration (h)<input type="number" step="1" min="24" data-w="hours" value="${dw.hours ?? 48}"></label>
      <p class="muted small">The average loads (never peaked) times the pattern, with any rain; with no rain this is an extended-period dry-weather run.</p></fieldset></div>` +
      (x ? `<div class="pd-ed"><label>Name<input data-k="name" value="${esc(x.name)}"></label><p class="muted small">24 hourly multipliers (mean ${num(x.hourly.reduce((a, c) => a + c, 0) / 24, 3)}; SWMM expects 1). Drag a bar or type a value.</p>
        <div class="pat-grid">${x.hourly.map((v, h) => `<label>${h}<input type="number" step="any" min="0" data-h="${h}" value="${v}"></label>`).join("")}</div><svg id="pat-svg" viewBox="0 0 480 140"></svg>
        <div class="row"><button data-a="norm">Scale to a mean of 1</button></div></div>` : `<div class="pd-ed muted">Add a pattern: 24 hourly multipliers of the average dry-weather flow.</div>`) + `</div>`;
    tag(b); bars();
  };
  const bars = () => {
    const svg = $("#pat-svg", b), x = draft[cur]; if (!svg || !x) return; const mx = Math.max(2, ...x.hourly) * 1.1;
    svg.innerHTML = x.hourly.map((v, h) => `<rect data-h="${h}" x="${h * 20 + 2}" y="${130 - v / mx * 120}" width="16" height="${v / mx * 120}" fill="#1f6feb" opacity=".8"/>`).join("") + `<line x1="0" x2="480" y1="${130 - 1 / mx * 120}" y2="${130 - 1 / mx * 120}" stroke="#c0392b" stroke-dasharray="4 3"/>`;
    svg.onpointerdown = ev => {
      const r = svg.getBoundingClientRect(), set = e2 => { const h = Math.max(0, Math.min(23, Math.floor((e2.clientX - r.left) / r.width * 24))); const ys = (e2.clientY - r.top) / r.height * 140, v = Math.max(0, (130 - ys) / 120 * mx); x.hourly[h] = +v.toFixed(2); const inp = $(`input[data-h="${h}"]`, b); if (inp) inp.value = x.hourly[h]; bars(); };
      set(ev); svg.setPointerCapture(ev.pointerId); svg.onpointermove = set; svg.onpointerup = () => { svg.onpointermove = null; };
    };
  };
  const collect = () => { const x = draft[cur]; if (!x) return; const n = $("[data-k=name]", b); if (n) x.name = n.value.trim() || x.name; for (const el of $$("input[data-h]", b)) x.hourly[+el.dataset.h] = Number(el.value || 0); };
  render(); d.hidden = false;
  b.oninput = e => { if (e.target.dataset.h != null) { collect(); bars(); } };
  d.onclick = e => {
    const t = e.target.closest("button"); if (!t) return;
    if (t.dataset.i != null) { collect(); cur = +t.dataset.i; render(); return; }
    const a = t.dataset.a || t.dataset.act; if (!a) return;
    if (a === "close") { d.hidden = true; return; }
    collect();
    if (a === "add") { draft.push({ name: `Pattern ${draft.length + 1}`, hourly: Array(24).fill(1) }); cur = draft.length - 1; render(); return; }
    if (a === "del") { draft.splice(cur, 1); cur = 0; render(); return; }
    if (a === "norm") { const x = draft[cur], m = x.hourly.reduce((s, v) => s + v, 0) / 24; if (m > 0) x.hourly = x.hourly.map(v => +(v / m).toFixed(3)); render(); return; }
    if (a === "ok") {
      const w = {}; for (const el of $$("[data-w]", b)) w[el.dataset.w] = el.type === "checkbox" ? el.checked : el.dataset.w === "hours" ? Number(el.value || 48) : (el.value || null);
      enqueue(async () => { await exec({ op: "batch", ops: [{ op: "set_setting", path: "libraries.patterns", value: draft }, { op: "set_setting", path: "swmm_dwf", value: w }] }); d.hidden = true; toast("Patterns and dry weather saved (one undo step).", "info"); });
    }
  };
}

/* ------------------------------------------------------------------ user notifications (F8) */
let notes = null;
async function runValidate() {
  if (!state.pid) { toast("Open a project first.", "info"); return; }
  notes = (await jget(`${base()}/validate`)).items;
  const err = notes.filter(n => n.level === "error").length, b = $("#notes-badge");
  b.hidden = !notes.length; b.textContent = notes.length; b.classList.toggle("err", err > 0);
  showTab("notes");
}
function renderNotes() {
  const tbl = $("#tbl-notes"); if (!tbl) return;
  if (!notes) { tbl.innerHTML = `<tbody><tr><td class="muted">Validate the model to list its errors and warnings.</td></tr></tbody>`; return; }
  const show = notes.filter(n => n.level === "error" || $("#notes-warn").checked);
  $("#notes-count").textContent = ` ${notes.filter(n => n.level === "error").length} errors, ${notes.filter(n => n.level === "warning").length} warnings`;
  tbl.innerHTML = `<thead><tr><th></th><th>Element</th><th>Message</th></tr></thead><tbody>` + (show.map((n, i) =>
    `<tr data-n="${notes.indexOf(n)}" class="note-${n.level}"><td>${n.level === "error" ? "&#9940;" : "&#9888;"}</td><td>${esc(n.id || "network")}</td><td>${esc(n.message)}</td></tr>`).join("") || `<tr><td></td><td colspan="2">Nothing to report.</td></tr>`) + `</tbody>`;
}

/* ------------------------------------------------------------------ selection sets (Ctrl+3) and queries (Ctrl+5) */
const selSets = () => (state.model && state.model.settings.selection_sets) || {};
async function saveSelectionSet() {
  if (!state.sel.ids.length) { toast("Select something first.", "info"); return; }
  const name = await askText("Selection set", `Name for these ${state.sel.ids.length} ${state.sel.table}`, `Set ${Object.keys(selSets()).length + 1}`); if (!name) return;
  const v = Object.assign({}, selSets(), { [name]: { table: state.sel.table, ids: state.sel.ids.slice() } });
  enqueue(async () => { await exec({ op: "set_setting", path: "selection_sets", value: v }); toast(`Selection set "${name}" saved with the project.`, "info"); });
}
function selSetMenu(x, y) {
  const S = selSets(), names = Object.keys(S);
  ctxOpen(x, y, [{ head: "Selection sets" }, ...(names.length ? names.map(n => ({ label: `${n} (${S[n].ids.length} ${S[n].table})`, key: "set-" + n, run: () => { const live = S[n].ids.filter(i => tmap(S[n].table).has(i)); setSel(S[n].table, live, { zoom: true }); } })) : [{ label: "No sets yet", disabled: true, run() {} }]),
    "-", { label: "Save the selection as a set...", key: "set-save", run: saveSelectionSet },
    ...(names.length ? [{ label: "Delete a set...", key: "set-del", run: async () => { const n = await askText("Delete a selection set", `One of: ${names.join(", ")}`, names[0]); if (!n || !S[n]) return; const v = Object.assign({}, S); delete v[n]; enqueue(() => exec({ op: "set_setting", path: "selection_sets", value: v })); } }] : [])]);
}
const Q_OPS = { "=": (a, b) => String(a) === String(b), "≠": (a, b) => String(a) !== String(b), ">": (a, b) => +a > +b, "≥": (a, b) => +a >= +b, "<": (a, b) => +a < +b, "≤": (a, b) => +a <= +b, "contains": (a, b) => String(a ?? "").toLowerCase().includes(String(b).toLowerCase()) };
function openQuery() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-query", "Query: select by a field", false), b = d.querySelector(".body");
  const fieldsOf = t => { const F = t === "nodes" ? state.model.nodeFeat : t === "links" ? state.model.linkFeat : state.model.catchFeat; const k = new Set(); for (const f of F.slice(0, 50)) for (const x of Object.keys(f.properties)) if (!x.startsWith("_") && typeof f.properties[x] !== "object") k.add(x); if (t === "links" && state.results) for (const r of Object.values(state.results.links || {}).slice(0, 5)) for (const x of Object.keys(r)) k.add(x); if (t === "nodes") k.add("load"); return [...k]; };
  const render = (t = "links") => {
    b.innerHTML = `<label>Elements<select id="q-t">${[["links", "pipes and pumps"], ["nodes", "structures"], ["catchments", "catchments"]].map(([v, l]) => `<option value="${v}"${v === t ? " selected" : ""}>${l}</option>`).join("")}</select></label>
      <label>Field<select id="q-f">${fieldsOf(t).map(f => `<option>${f}</option>`).join("")}</select></label>
      <label>Is<select id="q-o">${Object.keys(Q_OPS).map(o => `<option>${o}</option>`).join("")}</select></label><label>Value<input id="q-v" type="text"></label>
      <label>Result<select id="q-m"><option value="new">a new selection</option><option value="add">added to the selection</option><option value="within">within the selection</option></select></label>`;
    $("#q-t", b).onchange = e => render(e.target.value); tag(b);
  };
  render(); d.querySelector("[data-act=ok]").textContent = "Select"; d.hidden = false;
  d.onclick = e => {
    const a = e.target.dataset && e.target.dataset.act; if (!a) return; if (a === "close") { d.hidden = true; return; }
    const t = $("#q-t", b).value, f = $("#q-f", b).value, op = Q_OPS[$("#q-o", b).value], v = $("#q-v", b).value, mode = $("#q-m", b).value;
    const F = t === "nodes" ? state.model.nodeFeat : t === "links" ? state.model.linkFeat : state.model.catchFeat;
    const R = t === "links" ? srcLinks() : {}, ls = (state.model.loads[state.model.settings.design_load] || {});
    let ids = F.filter(x => { const val = f === "load" ? (ls[x.id] ?? 0) : x.properties[f] !== undefined ? x.properties[f] : (R[x.id] || {})[f]; return val !== undefined && val !== null && op(val, v); }).map(x => String(x.id));
    const cur = state.sel.table === t ? state.sel.ids : [];
    if (mode === "add") ids = [...new Set([...cur, ...ids])]; else if (mode === "within") ids = ids.filter(i => cur.includes(i));
    setSel(t, ids, { zoom: ids.length > 0 }); toast(`${f} ${$("#q-o", b).value} ${v}: ${ids.length} selected.`, "info");
  };
}

/* ------------------------------------------------------------------ FlexTables: the columns shown and a statistics row */
function tableFooter(kind, tbl, rows, cols) {
  if (kind === "toolout" || !rows.length) return;
  const num_ = c => rows.map(r => r[c]).filter(v => typeof v === "number" && isFinite(v));
  const cells = cols.map(c => { const v = num_(c).map(x => toShow(c, x)); if (!v.length || c === "id") return `<td>${c === cols[0] ? `<b>${rows.length}</b>` : ""}</td>`;
    const s = v.reduce((a, x) => a + x, 0); return `<td title="sum ${+s.toFixed(3)} · min ${+Math.min(...v).toFixed(3)} · max ${+Math.max(...v).toFixed(3)}">${+(s / v.length).toFixed(3)}<br><span class="muted small">${+Math.min(...v).toFixed(2)} – ${+Math.max(...v).toFixed(2)}</span></td>`; });
  tbl.insertAdjacentHTML("beforeend", `<tfoot><tr class="stats" title="Mean, and the range, of the rows shown (hover for the sum)">${cells.join("")}</tr></tfoot>`);
}
function columnsMenu(kind, x, y) {
  const all = new Set(colsOf(kind)), R = state.results ? Object.values(state.results.links || {})[0] || {} : {};
  const F = kind === "nodes" ? (state.model.nodeFeat[0] || {}).properties || {} : (state.model.linkFeat[0] || {}).properties || {};
  for (const k of Object.keys(kind === "results" ? R : F)) if (!k.startsWith("_") && typeof (kind === "results" ? R : F)[k] !== "object") all.add(k);
  if (kind === "nodes") all.add("load"); if (kind === "results") all.add("flags");
  const cur = new Set(colsOf(kind));
  ctxOpen(x, y, [{ head: "Columns" }, ...[...all].map(c => ({ label: (cur.has(c) ? "✓ " : "   ") + (LABELS[c] || c), key: "col-" + c, run: () => {
    const now = colsOf(kind).slice(), i = now.indexOf(c); if (i >= 0) { if (c !== "id") now.splice(i, 1); } else now.push(c);
    state.table[kind].cols = now; renderTable(kind); setTimeout(() => columnsMenu(kind, x, y), 0); } })),
    "-", { label: "Default columns", key: "col-reset", run: () => { state.table[kind].cols = null; renderTable(kind); } }]);
}

/* ------------------------------------------------------------------ wiring */
(function wireV3() {
  const sb = stormBlock, wb = wireStormBlock;
  stormBlock = function (t, fs) { return unitRowsBlock(t, fs) + sb(t, fs); };
  wireStormBlock = function (host) { wb(host); wireUnitRows(host); };
  for (const kind of ["nodes", "links", "results"]) {
    const bar = $(`#pane-${kind} .ptool`); if (!bar) continue;
    const btn = document.createElement("button"); btn.className = "tb"; btn.id = `cols-${kind}`; btn.textContent = "Columns..."; btn.title = "Choose the columns of this table";
    btn.onclick = e => { e.stopPropagation(); const r = btn.getBoundingClientRect(); columnsMenu(kind, r.left, Math.max(10, r.top - 320)); };
    bar.insertBefore(btn, bar.querySelector(".sp"));
  }
  $("#notes-run").onclick = () => enqueue(runValidate);
  $("#notes-warn").onchange = renderNotes;
  $("#tbl-notes").addEventListener("click", e => { const tr = e.target.closest("tr[data-n]"); if (!tr) return; const n = notes[+tr.dataset.n]; if (n.id && tmap(n.table).has(n.id)) setSel(n.table, [n.id], { zoom: true }); });
  document.addEventListener("keydown", e => {                       // SewerGEMS's manager shortcuts
    if (e.key === "F8") { e.preventDefault(); enqueue(runValidate); return; }
    if (!e.ctrlKey || e.shiftKey || e.altKey) return;
    const k = { "1": () => $("#sym-edit").click(), "3": () => selSetMenu(innerWidth / 2 - 120, 140), "4": () => navMenu(innerWidth / 2 - 120, 140), "5": openQuery, "6": openPrototypes, "7": () => showTab("links"), "9": () => showTab("profile") }[e.key];
    if (k && state.model) { e.preventDefault(); k(); }
  });
  tag();
})();
