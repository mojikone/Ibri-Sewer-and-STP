"use strict";
/* W19 v5 (2026-11-23, the engineer's F13-F20): a selection of any element types (All by default), selection sets as
   the scope of runs and edits, the tool hint as a fading tooltip, the Element Symbology pane docked on the left,
   Settings as dedicated managers with paste from Excel and named catalogues, and a Design constraints manager. */

/* ------------------------------------------------------------------ F13: a selection of any element types */
const MIX_ORDER = ["links", "nodes", "catchments"];
const MIX_NAME = { links: ["pipe", "pipes"], nodes: ["structure", "structures"], catchments: ["catchment", "catchments"] };
const mixCount = m => MIX_ORDER.reduce((s, t) => s + (m[t] || []).length, 0);
function currentMix() {
  if (state.mix) return { nodes: state.mix.nodes.slice(), links: state.mix.links.slice(), catchments: state.mix.catchments.slice() };
  const m = { nodes: [], links: [], catchments: [] }; if (state.sel.table) m[state.sel.table] = state.sel.ids.slice(); return m;
}
/* the selection becomes m (several types); Properties and the tables work on one type at a time, chosen in the bar */
function setMix(m, opt) {
  m = { nodes: [...new Set(m.nodes || [])], links: [...new Set(m.links || [])], catchments: [...new Set(m.catchments || [])] };
  const types = MIX_ORDER.filter(t => m[t].length);
  if (types.length <= 1) { state.mix = null; baseSetSel(types[0] || null, types[0] ? m[types[0]] : [], opt); return; }
  state.mix = m;
  const primary = types.includes(state.mixEdit) ? state.mixEdit : types[0];
  baseSetSel(primary, m[primary], Object.assign({}, opt, { _mix: true }));
}
function selClick(table, id, multi) {
  if (!multi) { setSel(table, [id]); return; }
  const m = currentMix(), a = m[table], k = a.indexOf(id);
  if (k >= 0) a.splice(k, 1); else a.push(id);
  setMix(m);
}
function deleteSelection() {
  const m = currentMix(), n = mixCount(m); if (!n) return;
  const ops = [];
  if (m.catchments.length) ops.push({ op: "delete", table: "catchments", ids: m.catchments });
  if (m.links.length) ops.push({ op: "delete", table: "links", ids: m.links });
  if (m.nodes.length) ops.push({ op: "delete", table: "nodes", ids: m.nodes });
  state.mix = null; state.sel = { table: null, ids: [] };
  enqueue(async () => { await exec(ops.length > 1 ? { op: "batch", ops } : ops[0]); toast(`${n} element${n > 1 ? "s" : ""} deleted (Ctrl+Z undoes).`, "info"); });
}
function mixBar() {
  if (!state.mix) return "";
  return `<div class="mix-bar" data-testid="mix-bar"><span>Selection:</span>` + MIX_ORDER.filter(t => state.mix[t].length).map(t =>
    `<button data-mix="${t}" class="${state.sel.table === t ? "on" : ""}" title="Show and edit the ${MIX_NAME[t][1]} of the selection">${state.mix[t].length} ${MIX_NAME[t][state.mix[t].length > 1 ? 1 : 0]}</button>`).join("") + `</div>`;
}

/* ------------------------------------------------------------------ F16: selection sets as the scope of runs and edits */
function setsMenuItems() {
  const S = selSets();
  return Object.keys(S).map(n => { const v = S[n]; const m = v.mix || (v.table ? { [v.table]: v.ids } : {});
    const live = { nodes: (m.nodes || []).filter(i => state.model.nodes.has(i)), links: (m.links || []).filter(i => state.model.links.has(i)), catchments: (m.catchments || []).filter(i => state.model.catchments.has(i)) };
    return { n, live, count: mixCount(live) }; });
}
function useSet(name, then) {
  const s = setsMenuItems().find(x => x.n === name); if (!s) return;
  setMix(s.live, { zoom: true }); if (then) then(s);
}

/* ------------------------------------------------------------------ F15: the hint as a tooltip by the cursor */
let hintMouse = { x: 0, y: 0 }, hintTimer = null;
function showHint() {
  const h = $("#hint"); if (!h || !h.textContent.trim()) return;
  const wrap = $("#map-wrap").getBoundingClientRect();
  h.classList.add("tip"); h.style.left = Math.min(Math.max(hintMouse.x - wrap.left + 16, 6), wrap.width - 330) + "px"; h.style.top = Math.max(hintMouse.y - wrap.top + 18, 6) + "px";
  h.classList.add("show"); clearTimeout(hintTimer); hintTimer = setTimeout(() => h.classList.remove("show"), 3500);
}

/* ------------------------------------------------------------------ F18: the Element Symbology pane on the left */
function symDock(on) {
  const r = $("#map-wrap").getBoundingClientRect(); document.body.style.setProperty("--dock-top", r.top + "px"); document.body.style.setProperty("--dock-bottom", (innerHeight - r.bottom) + "px");
  document.body.classList.toggle("sym-docked", on); if (on) symOpen(); else $("#dlg-sym").hidden = true;
  setTimeout(() => map.resize(), 30);
}

/* ------------------------------------------------------------------ F19 / F20: settings managers, paste, catalogues */
const SET_GROUPS = [
  ["Units", ["Units"]], ["Loads and peaking", ["Flows", "Peaking (extreme flows)", "Peaking factor table"]], ["Infiltration", ["Infiltration"]],
  ["Hydraulics", ["Friction", "Water profile and losses"]], ["Design constraints", ["Design limits", "Minimum gradient by size", "d/D limit by size", "Pipe catalogue"]],
  ["Force mains", ["Force mains", "Force mains (project)"]], ["Storm", ["Storm run", "Rain", "Dry weather on SWMM"]],
];
let setGroup = (() => { try { return localStorage.getItem("w19.setgroup") || "Design constraints"; } catch (e) { return "Design constraints"; } })();
function settingsNav() {
  const host = $("#settings-form"); if (!host || !host.querySelector("fieldset")) return;
  let nav = $("#set-nav");
  if (!nav) { nav = document.createElement("div"); nav.id = "set-nav"; $("#pane-settings").insertBefore(nav, host); $("#pane-settings").classList.add("with-nav"); }
  nav.innerHTML = SET_GROUPS.map(([g]) => `<button data-g="${esc(g)}" class="${g === setGroup ? "on" : ""}">${esc(g)}</button>`).join("") + `<button data-g="*" class="${setGroup === "*" ? "on" : ""}">Everything</button>`;
  nav.onclick = e => { const b = e.target.closest("button[data-g]"); if (!b) return; setGroup = b.dataset.g; try { localStorage.setItem("w19.setgroup", setGroup); } catch (x) {} settingsNav(); };
  const want = setGroup === "*" ? null : new Set((SET_GROUPS.find(g => g[0] === setGroup) || [0, []])[1]);
  for (const fs of $$("fieldset", host)) { const lg = (fs.querySelector("legend") || {}).textContent || ""; if (fs.parentElement === host || fs.id === "rain-box") fs.hidden = !!want && !want.has(lg.trim()); }
  catalogueControls(); pasteTables();
}
/* the group holding a setting is opened when something points at it (a ribbon button, a link) */
function revealSetting(el) {
  const fs = el && el.closest && el.closest("#settings-form > fieldset, #rain-box"); if (!fs || !fs.hidden) return;
  const lg = ((fs.querySelector("legend") || {}).textContent || "").trim(), g = SET_GROUPS.find(x => x[1].includes(lg));
  setGroup = g ? g[0] : "*"; settingsNav();
}
function openSettingsGroup(g) { setGroup = g; showTab("settings"); if (ui.bottomCollapsed) setBottom(false); setTimeout(settingsNav, 30); }
/* paste a block copied from Excel (two columns) into any settings table: it replaces the rows (Apply makes it final) */
function pasteTables() {
  for (const fs of $$(".tbl-set", $("#settings-form"))) {
    if (fs.dataset.paste) continue; fs.dataset.paste = "1";
    const rows_ = fs.querySelectorAll(".row"), row = rows_[rows_.length - 1]; if (row && !row.querySelector("[data-act=paste]")) row.insertAdjacentHTML("afterbegin", `<button class="tb2" data-act="paste" title="Paste two columns copied from Excel (or click a cell and press Ctrl+V)">Paste from Excel</button>`);
    const take = text => {
      const rows = text.replace(/\r/g, "").split("\n").map(l => (/[\t;]/.test(l) ? l.split(/[\t;]/).map(x => x.replace(/,/g, "")) : l.split(/,\s*|\s+/)).map(x => Number(String(x).trim())))   // Excel copies tab-separated: commas there are thousands separators.filter(r => r.length >= 2 && isFinite(r[0]) && isFinite(r[1])).map(r => [r[0], r[1]]);
      if (!rows.length) { toast("Nothing to paste: copy two columns of numbers from Excel.", "info"); return; }
      state.tableDraft[fs.dataset.tpath] = rows; $("#settings-form").dataset.sig = ""; renderSettings();
      toast(`${rows.length} rows pasted into ${(fs.querySelector("legend") || {}).textContent}: check them, then Apply.`, "info");
    };
    fs.addEventListener("paste", e => { const t = (e.clipboardData || window.clipboardData).getData("text"); if (/\t|\n/.test(t)) { e.preventDefault(); take(t); } });
    fs.addEventListener("click", async e => {
      if (e.target.dataset.act !== "paste") return; e.stopPropagation();
      try { take(await navigator.clipboard.readText()); }
      catch (x) { const t = await askText("Paste from Excel", "Paste the copied cells here (Ctrl+V), then OK", ""); if (t) take(t); }
    }, true);
  }
}
/* named pipe catalogues: one is the design catalogue; others are kept with the project to switch to */
function catalogueControls() {
  const fs = $("#tbl-design-catalogue"); if (!fs || fs.querySelector(".cat-bar")) return;
  const lib = (state.model.settings.libraries || {}).catalogues || {}, cur = state.model.settings.design.catalogue_name || "";
  fs.querySelector("legend").insertAdjacentHTML("afterend", `<div class="cat-bar row"><label>Catalogue<select id="cat-pick" data-testid="cat-pick"><option value="">${cur ? esc(cur) + " (in use)" : "(the one in use)"}</option>${Object.keys(lib).filter(n => n !== cur).map(n => `<option>${esc(n)}</option>`).join("")}</select></label>` +
    `<button class="tb2" id="cat-use" data-testid="cat-use">Use it</button><button class="tb2" id="cat-save" data-testid="cat-save" title="Keep the rows shown as a named catalogue">Save as...</button></div>`);
  $("#cat-save").onclick = async () => {
    const n = await askText("Pipe catalogue", "Name (e.g. PE100 SDR17, GRP SN10)", cur || "Catalogue 1"); if (!n) return;
    const rows = state.model.settings.design.catalogue, v = Object.assign({}, lib, { [n]: rows });
    enqueue(async () => { await exec({ op: "batch", ops: [{ op: "set_setting", path: "libraries.catalogues", value: v }, { op: "set_setting", path: "design.catalogue_name", value: n }] }); $("#settings-form").dataset.sig = ""; await loadModel(); renderSettings(); toast(`Catalogue "${n}" saved.`, "info"); });
  };
  $("#cat-use").onclick = () => {
    const n = $("#cat-pick").value; if (!n) return;
    enqueue(async () => { await exec({ op: "batch", ops: [{ op: "set_setting", path: "design.catalogue", value: lib[n] }, { op: "set_setting", path: "design.catalogue_name", value: n }] });
      state.info.catalogue = lib[n].map(r => r[0]); $("#settings-form").dataset.sig = ""; delete state.tableDraft["design.catalogue"]; await loadModel(); renderSettings(); toast(`The design now uses "${n}" (one undo step).`, "info"); });
  };
}

/* ------------------------------------------------------------------ wiring */
const baseSetSel = setSel;
(function wireV5() {
  setSel = function (table, ids, opt) { if (!(opt && opt._mix)) { state.mix = null; } baseSetSel(table, ids, opt); };
  const hb = highlight;
  highlight = async function () {
    await hb();
    if (!state.mix || !state.model) return;
    const L = [], N = [];
    for (const i of state.mix.links) { const f = state.model.links.get(i); if (f) L.push(f); }
    for (const i of state.mix.catchments) { const f = state.model.catchments.get(i); if (f) L.push(f); }
    for (const i of state.mix.nodes) { const f = state.model.nodes.get(i); if (f) N.push({ type: "Feature", geometry: f.geometry, properties: { _pend: 0 } }); }
    map.getSource("sel-links").setData({ type: "FeatureCollection", features: L }); map.getSource("sel-nodes").setData({ type: "FeatureCollection", features: N });
  };
  const rp = renderProps;
  renderProps = function () {
    rp(); const host = $("#prop-grid"); if (!host) return;
    const old = host.querySelector(".mix-bar"); if (old) old.remove();          // the in-place refresh keeps the grid: one bar
    if (!state.mix) return;
    host.insertAdjacentHTML("afterbegin", mixBar());
    host.querySelector(".mix-bar").onclick = e => { const b = e.target.closest("button[data-mix]"); if (!b) return; state.mixEdit = b.dataset.mix; gridSig = ""; setMix(state.mix); };
  };
  // the box and polygon tools select every type by default ("All")
  const st = $("#sel-target"); if (st && !st.querySelector("option[value=all]")) { st.insertAdjacentHTML("afterbegin", `<option value="all">all elements</option>`); st.value = "all"; }
  selWhat.target = "all";
  const si = selectInside;
  selectInside = function (target, inside, add) {
    if (target !== "all") { si(target, inside, add); return; }
    const m = { nodes: [], links: [], catchments: [] };
    for (const f of state.model.nodeFeat) if (inside(f.geometry.coordinates)) m.nodes.push(String(f.id));
    for (const f of state.model.linkFeat) { const c = f.geometry.coordinates, a0 = c[0], a1 = c[c.length - 1]; if (inside([(a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2])) m.links.push(String(f.id)); }
    for (const f of state.model.catchFeat) if (inside(centroidOf(ringOf(f)))) m.catchments.push(String(f.id));
    if (add) { const c = currentMix(); for (const t of MIX_ORDER) m[t] = [...c[t], ...m[t]]; }
    setMix(m); const n = mixCount(m);
    toast(`${n} selected: ` + MIX_ORDER.filter(t => m[t].length).map(t => `${m[t].length} ${MIX_NAME[t][m[t].length > 1 ? 1 : 0]}`).join(", ") + ". Ctrl or Shift click removes one; edit each kind in Properties.", "info");
  };
  // Ctrl/Shift drag with the Select tool: every type too
  // selection sets keep any types; selecting one selects them all
  saveSelectionSet = async function () {
    const m = currentMix(), n = mixCount(m); if (!n) { toast("Select something first.", "info"); return; }
    const name = await askText("Selection set", `Name for these ${n} elements`, `Set ${Object.keys(selSets()).length + 1}`); if (!name) return;
    const v = Object.assign({}, selSets(), { [name]: { mix: m, table: state.sel.table, ids: state.sel.ids.slice() } });
    enqueue(async () => { await exec({ op: "set_setting", path: "selection_sets", value: v }); toast(`Selection set "${name}" saved: use it to design, edit or check just those elements.`, "info"); });
  };
  selSetMenu = function (x, y) {
    const items = setsMenuItems();
    ctxOpen(x, y, [{ head: "Selection sets" }, ...(items.length ? items.flatMap(s => [
      { label: `${s.n} (${s.count})`, key: "set-" + s.n, title: "Select it", run: () => useSet(s.n) },
      { label: `   design only "${s.n}"`, key: "setdesign-" + s.n, title: "Design just these pipes (the rest kept)", run: () => useSet(s.n, () => { state.mixEdit = "links"; setMix(currentMix()); openDesignDlg(); const r = $("#des-scope-sel"); if (r) r.checked = true; }) },
      { label: `   check only "${s.n}"`, key: "setcheck-" + s.n, title: "The notifications of just these elements", run: () => useSet(s.n, sx => enqueue(async () => { await runValidate(); const ids = new Set([...sx.live.nodes, ...sx.live.links, ...sx.live.catchments]); notes = notes.filter(nn => ids.has(nn.id)); renderNotes(); })) }]) : [{ label: "No sets yet", disabled: true, run() {} }]),
      "-", { label: "Save the selection as a set...", key: "set-save", run: saveSelectionSet },
      ...(items.length ? [{ label: "Delete a set...", key: "set-del", run: async () => { const S = selSets(), names = Object.keys(S); const n = await askText("Delete a selection set", `One of: ${names.join(", ")}`, names[0]); if (!n || !S[n]) return; const v = Object.assign({}, S); delete v[n]; enqueue(() => exec({ op: "set_setting", path: "selection_sets", value: v })); } }] : [])]);
  };
  // the hint follows the cursor and fades (F15)
  map.on("mousemove", e => { hintMouse = { x: e.originalEvent.clientX, y: e.originalEvent.clientY }; });
  new MutationObserver(showHint).observe($("#hint"), { childList: true, characterData: true, subtree: true });
  // Settings as managers (F19, F20)
  const rs = renderSettings;
  renderSettings = function () { rs(); settingsNav(); };
  tag();
})();

/* ------------------------------------------------------------------ alternatives (F14), as SewerGEMS's */
async function openAlternatives() {
  if (!state.pid) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-alts", "Alternatives", true), b = d.querySelector(".body");
  d.querySelector("[data-act=ok]").hidden = true;
  const sid = state.sid;
  const draw = async () => {
    const A = await jget(`/projects/${state.pid}/alternatives`), me = A.scenarios[sid] || { alts: {}, own_edits: {} };
    b.innerHTML = `<p class="muted">An alternative is one kind of data (loads, pumps, settings...) kept under a name and shared by every scenario that takes it,
      with a parent it inherits from. A scenario that takes one for a kind uses it instead of its own edits of that kind, and what you change of that kind afterwards goes into the alternative.
      Scenario: <b>${esc(me.name || sid)}</b>.</p>
      <table class="tbl alt-tbl" data-testid="alt-table"><thead><tr><th>Kind</th><th>This scenario takes</th><th>Alternatives (used by)</th><th></th></tr></thead><tbody>` +
      A.categories.map(c => {
        const L = A.alternatives[c.id] || [], cur = me.alts[c.id] || "", own = me.own_edits[c.id] || 0;
        return `<tr data-cat="${c.id}"><td>${esc(c.name)}</td><td><select data-testid="alt-use-${c.id}"><option value="">Its own edits${own ? ` (${own})` : ""}</option>` +
          L.map(a => `<option value="${esc(a.id)}" ${a.id === cur ? "selected" : ""}>${esc(a.name)}</option>`).join("") + `</select></td><td class="muted">` +
          (L.length ? L.map(a => `<span class="alt-chip" title="${a.edits} edits${a.parent ? ", child of " + esc((L.find(x => x.id === a.parent) || {}).name || a.parent) : ""}">${esc(a.name)} <small>(${a.used_by.map(s => esc((A.scenarios[s] || {}).name || s)).join(", ") || "none"})</small>` +
            ` <button class="mini" data-act="ren" data-id="${esc(a.id)}" title="Rename">&#9998;</button><button class="mini" data-act="del" data-id="${esc(a.id)}" title="Delete">&times;</button></span>`).join(" ") : "none") +
          `</td><td><button class="mini" data-act="new" data-testid="alt-new-${c.id}" title="A new empty alternative${cur ? ", a child of the one this scenario takes" : ""}">New</button>` +
          (own ? `<button class="mini" data-act="from" data-testid="alt-from-${c.id}" title="A new alternative holding this scenario's own ${esc(c.name.toLowerCase())} edits">From this scenario</button>` : "") + `</td></tr>`;
      }).join("") + `</tbody></table>`;
  };
  await draw(); d.hidden = false;
  const after = async (msg) => { await refreshAll(); await draw(); if (msg) toast(msg, "info"); };
  b.onchange = e => {
    const s = e.target.closest("select"); if (!s) return; const cat = s.closest("tr").dataset.cat;
    enqueue(() => withBusy("Building the scenario...", async () => {
      const r = await jpost(`/projects/${state.pid}/scenarios/${sid}/alts`, { cat, aid: s.value || null });
      await after(r.skipped ? `${r.skipped} edits of this alternative name elements this scenario does not have: left out.` : "");
    }));
  };
  d.onclick = async e => {
    const t = e.target.closest("[data-act]"); if (!t) return; const a = t.dataset.act;
    if (a === "close") { d.hidden = true; return; }
    const tr = t.closest("tr"); if (!tr) return; const cat = tr.dataset.cat, cur = tr.querySelector("select").value || null;
    if (a === "new" || a === "from") {
      const name = await askText("New alternative", "Name", ""); if (name === null || name === undefined) return;
      enqueue(async () => {
        const r = await jpost(`/projects/${state.pid}/alternatives/new`, { cat, name: name || null, parent: a === "new" ? cur : null, from_scenario: a === "from" ? sid : null });
        await jpost(`/projects/${state.pid}/scenarios/${sid}/alts`, { cat, aid: r.created });
        await after(`This scenario now takes "${name || r.created}".`);
      });
    } else if (a === "ren") {
      const name = await askText("Rename the alternative", "Name", t.parentElement.firstChild.textContent.trim()); if (!name) return;
      enqueue(async () => { await jpost(`/projects/${state.pid}/alternatives/rename`, { cat, id: t.dataset.id, name }); await draw(); });
    } else if (a === "del") {
      enqueue(async () => { try { await jpost(`/projects/${state.pid}/alternatives/delete`, { cat, id: t.dataset.id }); await draw(); } catch (x) { toast(x.message || String(x)); } });
    }
  };
}

/* ------------------------------------------------------------------ the assistant's folders (F21) */
async function openAgentFolders() {
  const d = dlg("dlg-folders", "Folders the assistant may read", true), b = d.querySelector(".body");
  d.querySelector("[data-act=ok]").textContent = "Add folder"; d.querySelector("[data-act=ok]").hidden = false;
  const draw = async () => {
    const r = await jget("/assistant/folders");
    b.innerHTML = r.remote ? `<p class="muted">Folders are managed on the engineer's own computer only; over the shared link the assistant reads no folder.</p>` :
      `<p class="muted">The assistant reads only these folders (and their sub-folders) to build and run models: GIS layers, terrain, SWMM files, tables. It changes only projects and scenarios it made itself, each change one Undo step. Kept on this computer.</p>
       <ul class="fold-list" data-testid="folder-list">${r.folders.map(f => `<li><code>${esc(f)}</code> <button class="mini" data-rm="${esc(f)}" title="Remove">&times;</button></li>`).join("") || "<li class='muted'>none yet</li>"}</ul>
       <label>Folder path<input id="fold-path" data-testid="folder-path" placeholder="D:\\Data\\Ibri GIS" style="width:100%"></label>`;
    d.querySelector("[data-act=ok]").hidden = !!r.remote;
  };
  await draw(); d.hidden = false;
  d.onclick = async e => {
    const t = e.target.closest("[data-act],[data-rm]"); if (!t) return;
    if (t.dataset.act === "close") { d.hidden = true; return; }
    try {
      if (t.dataset.rm) await jpost("/assistant/folders/remove", { path: t.dataset.rm });
      else if (t.dataset.act === "ok") { const p = ($("#fold-path").value || "").trim(); if (!p) return; await jpost("/assistant/folders", { path: p }); toast("Folder added: ask the assistant to look in it.", "info"); }
      await draw();
    } catch (x) { toast(x.message || String(x)); }
  };
}
(function wireFolders() { const bt = $("#asst-folders"); if (bt) bt.addEventListener("click", openAgentFolders); })();

/* ------------------------------------------------------------------ the assistant's spending limit (v5) */
async function showBudget(b) {
  try { b = b || await jget("/assistant/usage"); } catch (e) { return; }
  const el = $("#asst-budget"); if (!el) return;
  el.textContent = `today ${b.spent_today_usd.toFixed(2)} of ${b.limit_today_usd.toFixed(2)} USD`;
  el.title = `${b.client}: ${b.remaining_usd.toFixed(2)} USD left today (resets at midnight)`;
  el.classList.toggle("warn", b.remaining_usd < 0.1 * b.limit_today_usd);
  const lb = $("#asst-limits"); if (lb) lb.hidden = !b.limits;               // only this computer sets the limits
  state.budget = b;
}
async function openLimits() {
  const b = await jget("/assistant/usage"); if (!b.limits) { toast("The limits are set on the engineer's computer.", "info"); return; }
  const d = dlg("dlg-limits", "Assistant spending limits", false), body = d.querySelector(".body"), L = b.limits;
  d.querySelector("[data-act=ok]").hidden = false; d.querySelector("[data-act=ok]").textContent = "Apply";
  const F = [["local_daily_usd", "This computer, per day"], ["web_daily_usd", "Each shared-link visitor, per day"], ["web_all_daily_usd", "All shared-link visitors together, per day"]];
  body.innerHTML = `<p class="muted">Estimated from the tokens of each answer at the model's list prices. An answer stops between steps when the limit is reached; 0 turns the assistant off for that group. Spent today here: ${b.spent_today_usd.toFixed(3)} USD; by visitors: ${b.web_all_spent_today_usd.toFixed(3)} USD.</p>` +
    F.map(([k, l]) => `<label>${l} (USD)<input type="number" min="0" step="0.5" data-k="${k}" data-testid="lim-${k}" value="${L[k]}"></label>`).join("");
  d.hidden = false;
  d.onclick = async e => {
    const a = e.target.dataset && e.target.dataset.act; if (!a) return; if (a !== "ok") { d.hidden = true; return; }
    const v = Object.fromEntries($$("input[data-k]", body).map(i => [i.dataset.k, Number(i.value)]));
    try { showBudget(await jpost("/assistant/limits", v)); d.hidden = true; toast("Limits applied.", "info"); } catch (x) { toast(x.message || String(x)); }
  };
}
(function wireBudget() {
  const lb = $("#asst-limits"); if (lb) lb.addEventListener("click", openLimits);
  const t = $("#tab-assistant"); if (t) t.addEventListener("click", () => showBudget());
  showBudget();
})();

/* ------------------------------------------------------------------ small screens (v5): the map keeps the screen */
(function responsive() {
  const small = () => innerWidth < 900 || innerHeight < 520;
  let was = null;
  const fit = () => {
    const s = small(); document.body.classList.toggle("compact-ui", s);
    if (s !== was) {
      if (s) {
        if (!ui.propsCollapsed) setProps(true);                                 // Properties waits as a strip on the right
        if (innerHeight < 520 || innerWidth < 600) {
          if (!ui.bottomCollapsed) setBottom(true);
          if (typeof rbCollapse === "function" && !ui.ribbonCollapsed) rbCollapse(true);    // a tap on a tab opens it
        }
        const lp = $("#legend-panel"); if (lp) lp.classList.add("folded");
      }
      was = s;
    }
    if (window.map) setTimeout(() => map.resize(), 60);
  };
  addEventListener("resize", () => { clearTimeout(fit.t); fit.t = setTimeout(fit, 120); });
  addEventListener("load", () => setTimeout(fit, 0));
  // on a small screen, choosing an element opens Properties as a drawer; a tap on the map closes it
  const ss = setSel;
  setSel = function (table, ids, opt) {
    const r = ss.apply(this, arguments);
    if (document.body.classList.contains("compact-ui") && !(opt && opt._mix)) {
      if (ids && ids.length === 1 && ui.propsCollapsed && state.tool === "select") setProps(false);   // chosen with Select: its properties (not on every manhole drawn)
      else if ((!ids || !ids.length) && !ui.propsCollapsed) setProps(true);             // nothing chosen: the map again
    }
    return r;
  };
  // a drawing tool picked on a small screen: the map, not Properties (the engineer, 2026-11-23)
  const st = setTool;
  setTool = function (t) {
    const r = st.apply(this, arguments);
    if (document.body.classList.contains("compact-ui") && t !== "select" && !ui.propsCollapsed) setProps(true);
    return r;
  };
})();
