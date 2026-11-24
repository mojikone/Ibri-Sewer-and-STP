/* W19 v5 (2026-11-23), the engineer's F28: terrain without uploading it.
   - A GeoTIFF picked on the engineer's own device is read IN THE BROWSER, a block at a time, only the blocks under the
     structures; the levels alone go to the server (trex/levels). A 7 GB terrain costs seconds and no upload.
   - A VRT is read the same way with its GeoTIFFs: picked together (one selection) or as its folder where the browser
     can open one. A phone cannot hand over a folder: it is told so and offered one GeoTIFF or Copernicus.
   - Copernicus GLO-30 (30 m, a surface model) is fetched by the server on request, only the cells around the network.
   - A terrain path on this computer (the old route) stays, for the app opened on this computer.
   Sampling matches the server's (rasterio): the cell that contains the point; a VRT source at another resolution is
   read bilinearly at the VRT cell's centre, as GDAL resamples it. Every level carries its source (Properties). */

const T6 = {
  pool: null,
  poolTried: false,
};
function t6Pool() {
  if (!T6.poolTried) { T6.poolTried = true; try { T6.pool = new GeoTIFF.Pool(Math.min(4, navigator.hardwareConcurrency || 2)); } catch (e) { T6.pool = null; } }
  return T6.pool;
}
const t6Phone = () => !window.showDirectoryPicker && matchMedia("(pointer: coarse)").matches;

/* ---- one GeoTIFF: its grid and a reader of single cells grouped by block */
async function t6Tiff(file) {
  const tiff = await GeoTIFF.fromBlob(file), img = await tiff.getImage(), fd = img.getFileDirectory();
  if (fd.ModelTransformation && (fd.ModelTransformation[1] || fd.ModelTransformation[4])) throw new Error(`${file.name}: a rotated grid is not read`);
  const gk = img.getGeoKeys() || {}, [rx, ry] = img.getResolution();
  let [ox, oy] = img.getOrigin();
  if (gk.GTRasterTypeGeoKey === 2) { ox -= rx / 2; oy -= ry / 2; }                 // PixelIsPoint: the tie point is a cell centre (as GDAL)
  const code = (gk.ProjectedCSTypeGeoKey && gk.ProjectedCSTypeGeoKey !== 32767) ? gk.ProjectedCSTypeGeoKey
             : (gk.GeographicTypeGeoKey && gk.GeographicTypeGeoKey !== 32767) ? gk.GeographicTypeGeoKey : null;
  const W = img.getWidth(), H = img.getHeight(), tiled = img.isTiled;
  const tw = tiled ? img.getTileWidth() : W, th = tiled ? img.getTileHeight() : (fd.RowsPerStrip || H);
  if (!tiled && tw * Math.min(th, H) * (fd.BitsPerSample ? fd.BitsPerSample[0] / 8 : 4) > 64e6)
    throw new Error(`${file.name} is stored in strips of ${Math.round(tw * th * 4 / 1e6)} MB: save it tiled (gdal_translate -co TILED=YES) or give its path on this computer`);
  const nd = img.getGDALNoData();
  /* the values of cells [[c, r], ...] (NaN off the grid or on no-data), each block decoded once */
  async function cells(cr, progress) {
    const out = new Float64Array(cr.length).fill(NaN), by = new Map();
    cr.forEach(([c, r], k) => { if (c < 0 || r < 0 || c >= W || r >= H) return; const key = `${Math.floor(c / tw)},${Math.floor(r / th)}`; (by.get(key) || by.set(key, []).get(key)).push(k); });
    let done = 0;
    for (const [key, ks] of by) {
      const [bx, bY] = key.split(",").map(Number), x0 = bx * tw, y0 = bY * th, x1 = Math.min(W, x0 + tw), y1 = Math.min(H, y0 + th);
      const opt = { window: [x0, y0, x1, y1], samples: [0] }; const pool = t6Pool(); if (pool) opt.pool = pool;
      let a;
      try { a = (await img.readRasters(opt))[0]; } catch (e) { if (!opt.pool) throw e; T6.pool = null; delete opt.pool; a = (await img.readRasters(opt))[0]; }
      for (const k of ks) { const v = a[(cr[k][1] - y0) * (x1 - x0) + (cr[k][0] - x0)]; out[k] = (nd !== null && v === nd) || !Number.isFinite(v) ? NaN : v; }
      if (progress) progress(++done, by.size);
    }
    return out;
  }
  return { name: file.name, crs: code ? `EPSG:${code}` : null, ox, oy, rx, ry, W, H, cells, res: Math.abs(rx) };
}

/* ---- a VRT: its grid and its Simple/Complex sources, matched by name among the files given */
function t6Vrt(text, name) {
  const x = new DOMParser().parseFromString(text, "application/xml"), root = x.querySelector("VRTDataset");
  if (!root) throw new Error(`${name} is not a VRT`);
  const gt = (root.querySelector(":scope > GeoTransform") || {}).textContent;
  if (!gt) throw new Error(`${name} has no GeoTransform`);
  const g = gt.split(",").map(Number); if (g[2] || g[4]) throw new Error(`${name}: a rotated grid is not read`);
  const band = root.querySelector("VRTRasterBand"); if (!band) throw new Error(`${name} has no band`);
  const other = [...band.children].filter(e => /Source$/.test(e.tagName) && !["SimpleSource", "ComplexSource"].includes(e.tagName));
  if (other.length) throw new Error(`${name}: ${other[0].tagName} sources are not read (only simple and complex ones)`);
  const num = (e, s, d) => { const v = e.querySelector(s); return v ? Number(v.textContent) : d; };
  const rect = e => e ? { x: +e.getAttribute("xOff"), y: +e.getAttribute("yOff"), w: +e.getAttribute("xSize"), h: +e.getAttribute("ySize") } : null;
  const sources = [...band.querySelectorAll(":scope > SimpleSource, :scope > ComplexSource")].map(s => {
    const fn = s.querySelector("SourceFilename").textContent.trim(), base = fn.split(/[\\/]/).pop();
    if (/\.vrt$/i.test(base)) throw new Error(`${name}: a VRT inside a VRT (${base}) is not read`);
    return { file: base, band: num(s, "SourceBand", 1), src: rect(s.querySelector("SrcRect")), dst: rect(s.querySelector("DstRect")),
             nodata: s.querySelector("NODATA") ? Number(s.querySelector("NODATA").textContent) : null,
             scale: num(s, "ScaleRatio", 1), offset: num(s, "ScaleOffset", 0) };
  });
  if (!sources.length) throw new Error(`${name} lists no source`);
  const srs = (root.querySelector(":scope > SRS") || {}).textContent || null;
  return { name, g, srs: srs && srs.trim(), nodata: num(band, "NoDataValue", null), sources };
}

/* ---- the levels at the structures: {id: level} plus the cell size, from a GeoTIFF or a VRT with its files */
async function terrainLevels(files, ids, progress) {
  files = [...files]; const vrtF = files.filter(f => /\.vrt$/i.test(f.name));
  if (vrtF.length > 1) throw new Error("pick one VRT at a time");
  let crs, sample, res, name;
  if (vrtF.length) {
    const V = t6Vrt(await vrtF[0].text(), vrtF[0].name), byName = new Map(files.map(f => [f.name.toLowerCase(), f]));
    const missing = [...new Set(V.sources.map(s => s.file))].filter(f => !byName.has(f.toLowerCase()));
    if (missing.length) throw new Error(`${V.name} reads ${missing.join(", ")}: pick ${missing.length > 1 ? "them" : "it"} together with the VRT (one selection in its folder)` +
                                        (t6Phone() ? ". On a phone a VRT does not work: pick one GeoTIFF, or use Copernicus" : ", or choose its folder"));
    const tif = new Map(); for (const s of V.sources) if (!tif.has(s.file)) tif.set(s.file, await t6Tiff(byName.get(s.file.toLowerCase())));
    crs = V.srs; res = Math.abs(V.g[1]); name = V.name;
    sample = async (X, Y) => {
      const n = X.length, val = new Float64Array(n).fill(NaN);
      for (let si = V.sources.length - 1; si >= 0; si--) {                  // later sources lie on top (GDAL paints in order)
        const s = V.sources[si], t = tif.get(s.file), d = s.dst || { x: 0, y: 0, w: t.W, h: t.H }, r = s.src || { x: 0, y: 0, w: t.W, h: t.H };
        const kx = r.w / d.w, ky = r.h / d.h, same = Math.abs(kx - 1) < 1e-12 && Math.abs(ky - 1) < 1e-12;
        const want = [], cr = [];
        for (let k = 0; k < n; k++) {
          if (!Number.isNaN(val[k])) continue;
          const px = (X[k] - V.g[0]) / V.g[1], py = (Y[k] - V.g[3]) / V.g[5];
          if (px < d.x || py < d.y || px >= d.x + d.w || py >= d.y + d.h) continue;
          if (same) { want.push([k, 1]); cr.push([r.x + Math.floor(px) - d.x, r.y + Math.floor(py) - d.y]); }
          else {                                                            // bilinear at the VRT cell's centre
            const fc = r.x + (Math.floor(px) + 0.5 - d.x) * kx - 0.5, fr = r.y + (Math.floor(py) + 0.5 - d.y) * ky - 0.5;
            const c0 = Math.floor(fc), r0 = Math.floor(fr), tx = fc - c0, ty = fr - r0, cl = (c, lo, hi) => Math.max(lo, Math.min(hi, c));
            const cx = [cl(c0, r.x, r.x + r.w - 1), cl(c0 + 1, r.x, r.x + r.w - 1)], ry = [cl(r0, r.y, r.y + r.h - 1), cl(r0 + 1, r.y, r.y + r.h - 1)];
            want.push([k, 4, tx, ty]); cr.push([cx[0], ry[0]], [cx[1], ry[0]], [cx[0], ry[1]], [cx[1], ry[1]]);
          }
        }
        if (!want.length) continue;
        const v = await t.cells(cr, progress), bad = z => Number.isNaN(z) || (s.nodata !== null && z === s.nodata);
        let j = 0;
        for (const w of want) {
          let z;
          if (w[1] === 1) z = bad(v[j]) ? NaN : v[j];
          else { const q = [v[j], v[j + 1], v[j + 2], v[j + 3]]; z = q.some(bad) ? NaN : q[0] * (1 - w[2]) * (1 - w[3]) + q[1] * w[2] * (1 - w[3]) + q[2] * (1 - w[2]) * w[3] + q[3] * w[2] * w[3]; }
          if (!Number.isNaN(z)) val[w[0]] = z * s.scale + s.offset;
          j += w[1];
        }
      }
      return val;
    };
  } else {
    const tf = files.filter(f => /\.tiff?$/i.test(f.name));
    if (tf.length !== 1) throw new Error("pick one GeoTIFF, or a VRT with its GeoTIFFs");
    const t = await t6Tiff(tf[0]); crs = t.crs; res = t.res; name = t.name;
    sample = async (X, Y) => t.cells(X.map((x, k) => [Math.floor((x - t.ox) / t.rx), Math.floor((Y[k] - t.oy) / t.ry)]), progress);
  }
  const p = await jpost(`${base()}/trex/points`, { crs, ids: ids && ids.length ? ids : null });
  const v = await sample(p.x, p.y), levels = {};
  p.ids.forEach((id, k) => { levels[id] = Number.isNaN(v[k]) ? null : v[k]; });
  return { levels, res, name, crs, noCrs: !crs };
}

/* ---- the dialog (replaces v4's) */
async function openTRex() {
  if (!state.model) { toast("Open a project first.", "info"); return; }
  const d = dlg("dlg-trex", "TRex: ground levels from terrain", true), b = d.querySelector(".body"); let files = null;
  const nsel = state.sel.table === "nodes" ? state.sel.ids.length : 0, local = !state.info.crs;
  const folder = !!window.showDirectoryPicker;
  b.innerHTML = `<p class="muted">Each structure's ground level from a terrain, one undo step. Where each level came from is kept with the structure (Properties).</p>
    <h5>A terrain on this device</h5>
    <p class="muted">A GeoTIFF, or a VRT picked together with its GeoTIFFs. It is read here, only the parts under the structures; nothing is uploaded, so its size does not matter.</p>
    <div class="row"><button data-a="files" data-testid="trex-files">Choose files...</button>${folder ? `<button data-a="folder" data-testid="trex-folder">Choose a VRT's folder...</button>` : ""}<span class="muted" id="trex-name">none</span></div>
    ${t6Phone() ? `<p class="muted" data-testid="trex-phone">On a phone a VRT does not work (it needs its folder): pick one GeoTIFF, or use Copernicus below.</p>` : ""}
    <label>or a terrain path on this computer (only when the app is opened on this computer)<input id="trex-path" type="text" placeholder="e.g. D:\\...\\IBRI_0p5_VRT2.vrt"></label>
    <h5>Copernicus 30 m (download)</h5>
    <p class="muted">A free worldwide surface model: roofs and trees are in it, its error is metres and its heights are above the EGM2008 geoid. For screening and a first layout, not for design levels; Validate counts the structures that rest on it. Only the cells around the network are read.</p>
    <div class="row"><button data-a="cop" data-testid="trex-cop"${local ? " disabled title=\"needs a project in a real coordinate system\"" : ""}>Fetch Copernicus 30 m and apply</button></div>
    <p class="muted small">Produced using Copernicus WorldDEM-30 &copy; DLR e.V. 2010-2014 and &copy; Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved. The organisations in charge of the Copernicus programme by law or by delegation do not incur any liability for any use of the Copernicus WorldDEM-30.</p>
    <h5>Options</h5>
    <label class="rad"><input type="checkbox" id="trex-keep" checked> Keep the depths (the inverts move with the ground)</label>
    <label class="rad"><input type="checkbox" id="trex-sel"${nsel ? "" : " disabled"}> Only the ${nsel || ""} selected structures</label><div id="trex-out"></div>`;
  d.querySelector("[data-act=ok]").textContent = "Apply"; d.hidden = false; tag(b);
  const out = $("#trex-out", b), ids = () => ($("#trex-sel", b).checked && state.sel.table === "nodes" ? state.sel.ids.slice() : null);
  const done = async (r, extra) => {
    out.innerHTML = `<div class="pump-res ok" data-testid="trex-done">${r.updated} structures from ${esc(r.source || "")}; mean change ${num(r.mean_change_m, 3)} m, largest ${num(r.max_change_m, 3)} m` +
      (r.no_data_count ? `; ${r.no_data_count} off the terrain or on no-data cells (kept)` : "") + `.${extra || ""}</div>`;
    updateScenario(r.scenario); if (state.storm) state.storm.stale = true; await loadModel(); await loadResults(); renderAll();
  };
  const fail = e => { out.innerHTML = `<div class="pump-res bad" data-testid="trex-error">${esc(e.message || String(e))}</div>`; };
  d.onclick = async e => {
    const t = e.target.closest("button"); if (!t) return; const a = t.dataset.a || t.dataset.act;
    if (a === "close") { d.hidden = true; return; }
    if (a === "files") {
      const i = document.createElement("input"); i.type = "file"; i.multiple = true; i.accept = ".tif,.tiff,.vrt";
      i.onchange = () => { files = [...i.files]; $("#trex-name", b).textContent = files.length ? files.map(f => f.name).join(", ") : "none"; out.innerHTML = ""; };
      i.click(); return;
    }
    if (a === "folder") {
      try {
        const h = await window.showDirectoryPicker({ mode: "read" }), fs = [];
        for await (const [n, fh] of h.entries()) if (fh.kind === "file" && /\.(vrt|tiff?)$/i.test(n)) fs.push(await fh.getFile());
        const v = fs.filter(f => /\.vrt$/i.test(f.name));
        files = v.length ? fs : fs.slice(0, 1);
        if (v.length > 1) { toast(`The folder has ${v.length} VRTs: the first, ${v[0].name}, is read.`, "info"); files = fs.filter(f => !/\.vrt$/i.test(f.name) || f === v[0]); }
        $("#trex-name", b).textContent = v.length ? `${v[0].name} and its folder` : files.length ? files[0].name : "no terrain in that folder";
      } catch (x) { if (x.name !== "AbortError") fail(x); }
      return;
    }
    if (a === "cop") {
      enqueue(() => withBusy("Fetching Copernicus 30 m...", async () => {
        try { const r = await jpost(`${base()}/trex/copernicus`, { keep_depth: $("#trex-keep", b).checked, ids: ids() }); await done(r, ` Tiles read: ${esc((r.tiles || []).join(", "))}.`); }
        catch (x) { fail(x); }
      }));
      return;
    }
    if (a === "ok") {
      const pth = $("#trex-path", b).value.trim();
      if (!files && !pth) { toast("Choose a terrain, give its path on this computer, or fetch Copernicus.", "info"); return; }
      enqueue(() => withBusy("Reading the terrain...", async () => {
        try {
          if (files && files.length) {
            const L = await terrainLevels(files, ids(), (k, n) => { if (k % 25 === 0 || k === n) out.textContent = `Reading the terrain: block ${k} of ${n}...`; });
            const r = await jpost(`${base()}/trex/levels`, { levels: L.levels, keep_depth: $("#trex-keep", b).checked, name: L.name, res_m: L.res });
            await done(r, L.noCrs ? " The terrain carries no coordinate system: it was taken to be in the project's." : "");
          } else {
            const qs = `keep_depth=${$("#trex-keep", b).checked}&ids=${encodeURIComponent((ids() || []).join(","))}&path=${encodeURIComponent(pth)}`;
            const res = await api(`${base()}/trex?${qs}`, { method: "POST", body: new FormData() }); await done(await res.json());
          }
        } catch (x) { fail(x); }
      }));
    }
  };
}
