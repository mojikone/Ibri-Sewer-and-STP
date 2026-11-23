"use strict";
/* W19 v4 (2026-11-23): LoadBuilder, TRex, control rules, the rational method, batch runs, calculation option sets,
   catchment hydrology and the GVF results in Properties. Loaded after features3.js. */

/* ------------------------------------------------------------------ a small file-picking helper */
function pickFile(accept) {
  return new Promise(res => { const i = document.createElement("input"); i.type = "file"; i.accept = accept; i.onchange = () => res(i.files[0] || null); i.click(); });
}
async function postFile(path, file) {
  const fd = new FormData(); fd.append("file", file);
  return (await api(path, { method: "POST", body: fd })).json();
}

/* ------------------------------------------------------------------ LoadBuilder */
async function openLoadBuilder() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-lb", "LoadBuilder: loads from a GIS layer", true), b = d.querySelector(".body"); let file = null, meta = null;
  const sets = Object.keys(state.model.loads || {}).concat(state.model.settings.design_load).filter((v, i, a) => a.indexOf(v) === i), units = unitLoads();
  const render = () => {
    b.innerHTML = `<p class="muted">Points (meters, buildings, people) or polygons (plots, by their centre) give each nearest manhole, wet well or storage the sum of a field, as SewerGEMS's LoadBuilder. Preview first; Apply is one undo step.</p>
      <div class="row"><button data-a="file" data-testid="lb-file">Choose a layer...</button><span class="muted">${file ? esc(file.name) + (meta ? ` · ${meta.features} features (${meta.geometry.join(", ")})` : "") : "GeoPackage, GeoJSON or a zipped shapefile"}</span></div>` +
      (meta ? `<label>Field<select id="lb-field">${meta.fields.map(f => `<option>${esc(f)}</option>`).join("")}</select></label>
      <label>Multiply by<input id="lb-scale" type="number" step="any" value="1"></label>
      <label>Becomes<select id="lb-target"><option value="load">the load of a load set, m3/d (each value x the factor)</option>${units.length ? `<option value="unit">a count of a unit load (each value x the factor)</option>` : ""}</select></label>
      <label id="lb-unit-l" hidden>Unit load<select id="lb-unit">${units.map(u => `<option>${esc(u.name)}</option>`).join("")}</select></label>
      <label>Load set<select id="lb-set">${sets.map(s => `<option${s === state.model.settings.design_load ? " selected" : ""}>${esc(s)}</option>`).join("")}</select></label>
      <label>Ignore beyond (m)<input id="lb-max" type="number" step="any" placeholder="no limit"></label>
      <div class="row"><button data-a="preview" class="primary" data-testid="lb-preview">Preview</button></div><div id="lb-out"></div>` : "");
    tag(b);
    const tg = $("#lb-target", b); if (tg) tg.onchange = () => { $("#lb-unit-l", b).hidden = tg.value !== "unit"; };
  };
  const q = apply => `${base()}/loadbuilder?field=${encodeURIComponent($("#lb-field", b).value)}&scale=${Number($("#lb-scale", b).value || 1)}&target=${$("#lb-target", b).value}` +
    `&unit=${encodeURIComponent(($("#lb-unit", b) || {}).value || "")}&load_set=${encodeURIComponent($("#lb-set", b).value)}&max_dist=${Number($("#lb-max", b).value || 0)}&apply=${apply}`;
  render(); d.querySelector("[data-act=ok]").textContent = "Apply"; d.hidden = false;
  d.onclick = async e => {
    const t = e.target.closest("button"); if (!t) return; const a = t.dataset.a || t.dataset.act;
    if (a === "close") { d.hidden = true; return; }
    if (a === "file") { file = await pickFile(".gpkg,.geojson,.json,.zip"); if (!file) return; meta = null; render();
      try { meta = await postFile(`${base()}/loadbuilder`, file); if (!meta.fields.length) { toast("The layer has no numeric field to take loads from.", "info"); meta = null; } } catch (x) { toast(x.message); } render(); return; }
    if (!meta) return;
    if (a === "preview" || a === "ok") {
      enqueue(async () => {
        const r = await postFile(q(a === "ok"), file), rp = r.report, unit = r.target === "unit" ? "units" : "m3/d";
        $("#lb-out", b).innerHTML = `<div class="pump-res ${rp.applied ? "ok" : ""}"><b>${rp.applied ? "Applied" : "Preview"}:</b> ${rp.used} of ${rp.features} features to ${rp.structures} structures, ${num(rp.total, 3)} ${unit} in all` +
          (rp.too_far ? `; ${rp.too_far} beyond the distance` : "") + (rp.no_value ? `; ${rp.no_value} with no value` : "") + `; farthest ${num(rp.max_distance_m, 1)} m.<br>Largest: ${r.top.slice(0, 6).map(x => `${esc(x.id)} ${num(x.value, 2)}`).join(", ")}</div>`;
        if (rp.no_crs) toast("The layer has no coordinate system: its coordinates were taken as the project's.", "info");
        if (rp.applied) { updateScenario(r.scenario); if (state.storm) state.storm.stale = true; await loadModel(); await loadResults(); renderAll(); toast("Loads applied (one undo step).", "info"); }
      });
    }
  };
}

/* ------------------------------------------------------------------ TRex */
async function openTRex() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-trex", "TRex: ground levels from terrain", false), b = d.querySelector(".body"); let file = null;
  const nsel = state.sel.table === "nodes" ? state.sel.ids.length : 0;
  b.innerHTML = `<p class="muted">Each structure's ground level from a terrain GeoTIFF (reprojected when its CRS differs). One undo step.</p>
    <div class="row"><button data-a="file" data-testid="trex-file">Choose a GeoTIFF...</button><span class="muted" id="trex-name">none</span></div>
    <label>or a terrain on this computer<input id="trex-path" type="text" placeholder="e.g. D:\...\IBRI_0p5_VRT2.vrt (large VRTs: give the path)"></label>
    <label class="rad"><input type="checkbox" id="trex-keep" checked> Keep the depths (the inverts move with the ground)</label>
    <label class="rad"><input type="checkbox" id="trex-sel"${nsel ? "" : " disabled"}> Only the ${nsel || ""} selected structures</label><div id="trex-out"></div>`;
  d.querySelector("[data-act=ok]").textContent = "Apply"; d.hidden = false; tag(b);
  d.onclick = async e => {
    const t = e.target.closest("button"); if (!t) return; const a = t.dataset.a || t.dataset.act;
    if (a === "close") { d.hidden = true; return; }
    if (a === "file") { file = await pickFile(".tif,.tiff"); $("#trex-name", b).textContent = file ? file.name : "none"; return; }
    if (a === "ok") {
      const pth = $("#trex-path", b).value.trim();
      if (!file && !pth) { toast("Choose a terrain GeoTIFF, or give a terrain file's path.", "info"); return; }
      const ids = $("#trex-sel", b).checked && state.sel.table === "nodes" ? state.sel.ids.join(",") : "";
      enqueue(async () => {
        const qs = `keep_depth=${$("#trex-keep", b).checked}&ids=${encodeURIComponent(ids)}` + (pth ? `&path=${encodeURIComponent(pth)}` : "");
        const r = pth ? await (await api(`${base()}/trex?${qs}`, { method: "POST", body: new FormData() })).json() : await postFile(`${base()}/trex?${qs}`, file);
        $("#trex-out", b).innerHTML = `<div class="pump-res ok">${r.updated} structures; mean change ${num(r.mean_change_m, 3)} m, largest ${num(r.max_change_m, 3)} m` + (r.no_data_count ? `; ${r.no_data_count} off the terrain or on no-data cells (kept)` : "") + `.</div>`;
        updateScenario(r.scenario); if (state.storm) state.storm.stale = true; await loadModel(); await loadResults(); renderAll();
      });
    }
  };
}

/* ------------------------------------------------------------------ control rules (storm run) */
function openControls() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-ctl", "Controls (storm run)", true), b = d.querySelector(".body");
  const links = state.model.linkFeat.filter(f => ["pump", "orifice", "weir"].includes(f.properties.kind)).map(f => [String(f.id), f.properties.kind]);
  const nodes = state.model.nodeFeat.map(f => String(f.id));
  const draft = JSON.parse(JSON.stringify(state.model.controls || []));
  const render = () => {
    b.innerHTML = `<p class="muted">Rules SWMM applies at each step: IF a structure's depth (m) or the time (h) passes a value THEN a pump is switched ON or OFF, or an orifice or weir opened to a setting (0 to 1); ELSE optional. They act with the pumps' start and stop depths.</p>
      <table class="lib-tab"><thead><tr><th>If</th><th>Structure</th><th></th><th>Value</th><th>Then</th><th>To</th><th>Else</th><th></th></tr></thead><tbody>` +
      draft.map((r, i) => `<tr data-i="${i}"><td><select data-f="if"><option value="node"${r.if === "node" ? " selected" : ""}>depth at</option><option value="time"${r.if === "time" ? " selected" : ""}>time (h)</option></select></td>` +
        `<td>${r.if === "node" ? `<select data-f="node">${nodes.map(n => `<option${n === r.node ? " selected" : ""}>${esc(n)}</option>`).join("")}</select>` : ""}</td>` +
        `<td><select data-f="op">${[">", ">=", "<", "<="].map(o => `<option${o === r.op ? " selected" : ""}>${o}</option>`).join("")}</select></td><td><input data-f="value" type="number" step="any" value="${r.value ?? ""}"></td>` +
        `<td><select data-f="link">${links.map(([l, k]) => `<option value="${esc(l)}"${l === r.link ? " selected" : ""}>${k} ${esc(l)}</option>`).join("")}</select></td>` +
        `<td><input data-f="then" value="${esc(r.then ?? "ON")}" style="width:60px"></td><td><input data-f="else" value="${esc(r.else ?? "")}" style="width:60px" placeholder="none"></td><td><button data-a="del">&times;</button></td></tr>`).join("") +
      `</tbody></table><div class="row"><button data-a="add" data-testid="ctl-add"${links.length ? "" : " disabled"}>Add a rule</button><span class="muted small">${links.length ? "Pumps: ON / OFF. Orifices and weirs: a setting 0-1." : "Draw a pump, orifice or weir first."}</span></div>`;
    tag(b);
  };
  const collect = () => { for (const tr of $$("tr[data-i]", b)) { const r = draft[+tr.dataset.i]; for (const el of $$("[data-f]", tr)) r[el.dataset.f] = el.dataset.f === "value" ? Number(el.value) : el.value; if (r.if === "time") delete r.node; if (r.else === "") delete r.else; } };
  render(); d.hidden = false;
  b.onchange = e => {
    const f = e.target.dataset.f; if (f !== "if" && f !== "link") return; collect();
    if (f === "link") { const r = draft[+e.target.closest("tr").dataset.i], pump = state.model.links.get(r.link).properties.kind === "pump"; r.then = pump ? "ON" : "1"; r.else = pump ? "OFF" : "0"; }
    render();
  };
  d.onclick = e => {
    const t = e.target.closest("button"); if (!t) return; const a = t.dataset.a || t.dataset.act; if (!a) return;
    if (a === "close") { d.hidden = true; return; }
    collect();
    if (a === "ok" && draft.some(r => !isFinite(r.value) || $$("tr[data-i] [data-f=value]", b).some(x => x.value === ""))) { toast("Give every rule a value."); return; }
    if (a === "add") { const pump = links.find(l => l[1] === "pump"), lk = (pump || links[0])[0], f = state.model.links.get(lk); draft.push({ if: "node", node: f.properties.from_node, op: ">", value: 1.5, link: lk, then: (pump ? "ON" : "1"), else: (pump ? "OFF" : "0") }); render(); return; }
    if (a === "del") { draft.splice(+t.closest("tr").dataset.i, 1); render(); return; }
    if (a === "ok") enqueue(async () => { await exec({ op: "set_controls", rules: draft }); await loadModel(); d.hidden = true; toast(`${draft.length} control rule${draft.length === 1 ? "" : "s"} saved (one undo step).`, "info"); });
  };
}

/* ------------------------------------------------------------------ the rational method, batch runs, calculation option sets */
async function runRational() {
  if (!state.pid) return;
  const r = await jget(`${base()}/rational`);
  state.toolout = { tool: { label: "Rational method (steady storm): Q = C i A / 360" }, rows: r.rows, cols: ["id", "q_rational_ls", "ca_ha", "tc_min", "i_mm_h", "v_ms", "d_over_D", "surcharged"], report: r.report };
  showTab("toolout"); renderAll();
}
function openBatch() {
  if (!state.info) return;
  const d = dlg("dlg-batch", "Batch run", false), b = d.querySelector(".body");
  b.innerHTML = `<p class="muted">The steady run of the scenarios ticked, side by side in Tool output.</p>` + state.info.scenarios.map(s => `<label class="rad"><input type="checkbox" value="${esc(s.id)}" checked> ${esc(s.name)}</label>`).join("");
  d.querySelector("[data-act=ok]").textContent = "Run"; d.hidden = false;
  d.onclick = e => {
    const a = e.target.dataset && e.target.dataset.act; if (!a) return; d.hidden = true; if (a !== "ok") return;
    const sids = $$("input[type=checkbox]", b).filter(x => x.checked).map(x => x.value);
    enqueue(() => withBusy("Batch run...", async () => {
      const r = await jpost(`/projects/${state.pid}/batch`, { sids });
      state.toolout = { tool: { label: "Batch run: steady results by scenario" }, rows: r.rows, cols: ["id", "scenario", "conduits", "km", "over_limit", "over_vmax", "surcharged", "km_under_vmin", "pumps_short", "flooding_nodes", "problems", "seconds"] };
      showTab("toolout"); renderAll();
    }));
  };
}
const CALC_KEYS = ["friction.method", "friction.ks_mm", "friction.manning_n", "peaking.method", "peaking.constant", "peaking.cutoff", "infiltration_m3d_per_km", "flow_profile", "structure_loss.K",
  "pressure.method", "pressure.C", "pressure.e_mm", "pressure.n", "pressure.suction", "pressure.use_pumped_flows", "storm_infiltration", "design_load", "check_load"];
function calcMenu(x, y) {
  const S = state.model.settings, sets = S.calc_option_sets || {}, get = p => p.split(".").reduce((o, k) => (o == null ? o : o[k]), S);
  ctxOpen(x, y, [{ head: "Calculation options" },
    ...Object.keys(sets).map(n => ({ label: `Apply "${n}" to this scenario`, key: "co-" + n, run: () => enqueue(async () => {
      await exec({ op: "batch", ops: Object.entries(sets[n]).map(([path, value]) => ({ op: "set_setting", path, value })) }); $("#settings-form").dataset.sig = ""; await loadModel(); await loadResults(); renderAll(); toast(`Calculation options "${n}" applied (one undo step).`, "info"); }) })),
    "-", { label: "Save the current options as...", key: "co-save", run: async () => {
      const n = await askText("Calculation options", "Name of this set of options", `Options ${Object.keys(sets).length + 1}`); if (!n) return;
      const v = Object.assign({}, sets, { [n]: Object.fromEntries(CALC_KEYS.map(k => [k, get(k)]).filter(([, x]) => x !== undefined)) });
      enqueue(async () => { await exec({ op: "set_setting", path: "calc_option_sets", value: v }); toast(`Options "${n}" saved with the project.`, "info"); }); } },
    { label: "Edit the options (Settings)", run: () => { if (typeof openSettingsGroup === "function") openSettingsGroup("*"); else { showTab("settings"); if (ui.bottomCollapsed) setBottom(false); } } }]);
}

/* ------------------------------------------------------------------ catchment hydrology and GVF results in Properties */
function hydroBlock(table, fs) {
  if (table !== "catchments") return "";
  const one = k => { const v = (fs[0].properties.hydro || {})[k]; return fs.every(f => (f.properties.hydro || {})[k] === v) ? v : undefined; };
  const h = { C: one("C"), tc_min: one("tc_min"), cn: one("cn") };
  return `<h5>Hydrology</h5><div class="pr"><label for="hy-C" title="Rational method">Runoff coefficient C</label><input type="number" step="any" min="0" max="1" id="hy-C" value="${h.C ?? ""}"><span class="u"></span></div>` +
    `<div class="pr"><label for="hy-tc">Time of concentration</label><input type="number" step="any" min="0" id="hy-tc" value="${h.tc_min ?? ""}"><span class="u">min</span></div>` +
    `<div class="pr"><label for="hy-cn" title="SCS curve number, for the storm run with curve-number infiltration">Curve number CN</label><input type="number" step="any" min="0" max="100" id="hy-cn" value="${h.cn ?? ""}"><span class="u"></span></div>` +
    `<div class="row"><button id="hy-apply" data-testid="hy-apply">Apply${fs.length > 1 ? ` to ${fs.length} catchments` : ""}</button><span class="muted small">${fs.length > 1 ? "blank: kept as it is" : ""}</span></div>`;
}
function gvfBlock(table, fs) {
  if (fs.length !== 1 || !state.results) return "";
  if (table === "nodes") { const n = (state.results.nodes || {})[fs[0].id]; if (!n) return "";
    return `<div class="pump-res${n.flooding ? " bad" : ""}" data-testid="node-hgl">Water level (GVF): <b>${num(n.hgl, 3)} m</b>${n.flooding ? " · ABOVE GROUND" : ` · ${num((fs[0].properties.ground ?? 0) - n.hgl, 2)} m below ground`}</div>`; }
  if (table === "links") { const r = (state.results.links || {})[fs[0].id]; if (!r || r.hgl_up == null) return "";
    return `<div class="pump-res${r.surcharged_gvf ? " bad" : ""}" data-testid="link-gvf">GVF: ${esc(r.regime || "")}; water ${num(r.hgl_up, 3)} to ${num(r.hgl_dn, 3)} m (depth ${num(r.y_up_m, 3)} to ${num(r.y_dn_m, 3)} m)${r.surcharged_gvf ? "; SURCHARGED" : ""}</div>`; }
  return "";
}
(function wireV4() {
  const sb = stormBlock, wb = wireStormBlock;
  stormBlock = function (t, fs) { return gvfBlock(t, fs) + hydroBlock(t, fs) + sb(t, fs); };
  wireStormBlock = function (host) {
    wb(host);
    const ha = $("#hy-apply", host);
    if (ha) ha.onclick = () => { const many = state.sel.ids.length > 1, o = {};
      for (const [k, el] of [["C", "C"], ["tc_min", "tc"], ["cn", "cn"]]) { const x = $("#hy-" + el, host).value; if (x !== "") o[k] = Number(x); else if (!many) o[k] = null; }
      enqueue(() => exec({ op: "set_hydrology", ids: state.sel.ids.slice(), ...o })); };
  };
  tag();
})();
