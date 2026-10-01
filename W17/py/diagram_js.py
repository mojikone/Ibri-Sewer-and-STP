"""Write the Figma Plugin API code that draws the transfer diagram(s) of given options from results/diagrams.json.

    python diagram_js.py S1            -> results/figma_S1.js
    python diagram_js.py S2 S3 S4      -> results/figma_S2_S3_S4.js
The frame of each option is placed at y = its row in the page (option index x 1600 px), so reruns replace in place.
Text is measured after it is set (natural width), centred by computation, and every line is checked against its box,
the frame, the arrows' vertical runs and every other line; the code returns the list of problems, empty when clean.
"""
import json, sys

SRC = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\diagrams.json"
names = sys.argv[1:] or ["S1"]
D = [d for d in json.load(open(SRC, encoding="utf-8")) if d["option"] in names]
order = {f"S{i}": i - 1 for i in range(1, 8)}
for d in D:
    d["y0"] = order[d["option"]] * 1600

JS = r"""
const D = __DATA__;
const ZONE = {O1:"#2E75B6", O4:"#C0504D", O9:"#70AD47", O3:"#7030A0", O16:"#ED7D31", O22:"#00A6D6"};
const RED = "#A61B1B", NAVY = "#1F3B63", GREY = "#5A5A5A";
const hex = h => ({r: parseInt(h.slice(1,3),16)/255, g: parseInt(h.slice(3,5),16)/255, b: parseInt(h.slice(5,7),16)/255});
await Promise.all([figma.loadFontAsync({family:"Inter", style:"Regular"}), figma.loadFontAsync({family:"Inter", style:"Bold"})]);
const page = figma.currentPage;
const out = [];
for (const d of D) {
  const F = d.font, name = `W17 ${d.option} transfer diagram`;
  for (const old of page.children.filter(n => n.name === name)) old.remove();
  const fr = figma.createFrame();
  fr.name = name; fr.resize(Math.round(d.width), Math.round(d.height)); fr.x = 0; fr.y = d.y0;
  fr.fills = [{type:"SOLID", color:{r:1,g:1,b:1}}]; fr.clipsContent = true;
  const issues = [], texts = [], buses = [];
  const pos = {}; for (const n of d.nodes) pos[n.id] = n;
  const text = (s, size, opts = {}) => {
    const t = figma.createText();
    t.fontName = {family:"Inter", style: opts.bold ? "Bold" : "Regular"}; t.characters = s; t.fontSize = size;
    t.fills = [{type:"SOLID", color: hex(opts.color || NAVY)}]; t.textAutoResize = "WIDTH_AND_HEIGHT";
    fr.appendChild(t); texts.push(t); return t;
  };
  const inBox = (n, s, top, size, opts) => {
    const t = text(s, size, opts);
    t.x = n.x + (n.w - t.width) / 2; t.y = n.y + top;
    if (t.width > n.w - 8) issues.push(`too wide for box ${n.id}: ${s}`);
    if (t.y + t.height > n.y + n.h + 0.5) issues.push(`below box ${n.id}: ${s}`);
  };
  const line = (pts, col, w) => {
    const v = figma.createVector();
    const minx = Math.min(...pts.map(p => p[0])), miny = Math.min(...pts.map(p => p[1]));
    v.vectorPaths = [{windingRule: "NONE", data: pts.map((p, i) => `${i ? "L" : "M"} ${p[0] - minx} ${p[1] - miny}`).join(" ")}];
    v.x = minx; v.y = miny; v.fills = []; v.strokes = [{type:"SOLID", color: hex(col)}]; v.strokeWeight = w;
    v.strokeJoin = "MITER"; fr.appendChild(v); return v;
  };
  const head = (x, y, col, h) => {  // arrowhead pointing right, tip at (x, y)
    const v = figma.createVector();
    v.vectorPaths = [{windingRule: "NONZERO", data: `M 0 0 L ${h} ${h / 2} L 0 ${h} Z`}];
    v.x = x - h; v.y = y - h / 2; v.fills = [{type:"SOLID", color: hex(col)}]; v.strokes = []; fr.appendChild(v);
  };
  // entry points: a subnetwork takes all its arrows at mid-height (one bus, one head); a plant spreads them
  const entry = {};
  for (const n of d.nodes) {
    const kids = d.edges.filter(e => e.dst === n.id).sort((a, b) => pos[a.src].y - pos[b.src].y);
    kids.forEach((e, i) => entry[e.src] = n.kind === "plant" ? n.y + n.h * (i + 1) / (kids.length + 1) : n.y + n.h / 2);
  }
  for (const e of d.edges) {
    const a = pos[e.src], b = pos[e.dst], col = e.kind === "gravity" ? NAVY : RED, w = e.kind === "gravity" ? 3 : 2;
    const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x, y2 = entry[e.src], xm = x2 - 30, hh = e.kind === "gravity" ? 15 : 13;
    line([[x1, y1], [xm, y1], [xm, y2], [x2 - hh + 1, y2]], col, w);
    head(x2, y2, col, hh);
    buses.push(xm);
    const t = text(e.label, F.edge, {color: col, bold: e.kind === "gravity"});
    t.x = x1 + 8; t.y = y1 - t.height - 3;
    if (t.x + t.width > xm - 4) issues.push(`label crosses the bus: ${e.src} ${e.label}`);
  }
  for (const n of d.nodes) {
    const r = figma.createRectangle(); r.resize(n.w, n.h); r.x = n.x; r.y = n.y; r.cornerRadius = 6;
    const c = hex(ZONE[n.zone] || "#555555");
    if (n.kind === "plant") { r.fills = [{type:"SOLID", color: hex(NAVY)}]; r.strokes = []; }
    else { r.fills = [{type:"SOLID", color: c, opacity: 0.14}]; r.strokes = [{type:"SOLID", color: c}]; r.strokeWeight = 1.6; }
    fr.appendChild(r);
    if (n.kind === "plant") {  // a band in the colour of the plant's subnetworks
      const band = figma.createRectangle(); band.resize(n.w, 6); band.x = n.x; band.y = n.y; band.topLeftRadius = 6; band.topRightRadius = 6;
      band.fills = [{type:"SOLID", color: c}]; band.strokes = []; fr.appendChild(band);
    }
    if (n.kind === "plant") {
      inBox(n, n.lines[0], 10, F.plant_title, {bold: true, color: "#FFFFFF"});
      inBox(n, n.lines[1], 36, F.plant, {color: "#C9D6EA"});
      inBox(n, n.lines[2], 56, F.plant, {color: "#FFFFFF"});
      inBox(n, n.lines[3], 76, F.plant, {color: "#FFFFFF"});
    } else {
      inBox(n, n.lines[0], 3, F.name, {bold: true});
      inBox(n, n.lines[1], 27, F.old, {color: GREY});
    }
  }
  // legend, left to right, wrapping when the row is full
  const plants = d.nodes.filter(n => n.kind === "plant"), zc = hex(ZONE[plants[0].zone] || "#555555");
  const L = F.legend, items = [
    {kind: "box", s: "Subnetwork: W17 name (modeller's outfall name)" + (plants.length > 1 ? ", coloured by its plant" : "")},
    {kind: "pumped", s: "Pumping station at the outfall and its rising main, 2070 peak flow"},
    {kind: "gravity", s: "Gravity: the plant sits at this subnetwork's own outfall"},
    {kind: "plant", s: "Treatment plant, flows 2030 → 2070"}];
  let lx = 40, ly = d.body + 10;
  for (const it of items) {
    const t = text(it.s, L, {color: GREY});
    const sw = 62, need = sw + 10 + t.width;
    if (lx + need > d.width - 40) { lx = 40; ly += 40; }
    const cy = ly + t.height / 2;
    if (it.kind === "box" || it.kind === "plant") {
      const r = figma.createRectangle(); r.resize(sw, 28); r.x = lx; r.y = cy - 14; r.cornerRadius = 4;
      if (it.kind === "plant") { r.fills = [{type:"SOLID", color: hex(NAVY)}]; r.strokes = []; }
      else { r.fills = [{type:"SOLID", color: zc, opacity: 0.14}]; r.strokes = [{type:"SOLID", color: zc}]; r.strokeWeight = 1.6; }
      fr.appendChild(r);
    } else {
      const col = it.kind === "gravity" ? NAVY : RED, hh = it.kind === "gravity" ? 15 : 13;
      line([[lx, cy], [lx + sw - hh + 1, cy]], col, it.kind === "gravity" ? 3 : 2); head(lx + sw, cy, col, hh);
    }
    t.x = lx + sw + 10; t.y = ly; lx += need + 44;
  }
  // checks: inside the frame, no two lines of text overlap, no text crossed by a vertical bus
  fr.resize(fr.width, Math.ceil(ly + 50));  // the legend's last row sets the height
  for (const t of texts) {
    if (t.x < 0 || t.y < 0 || t.x + t.width > fr.width + 0.5 || t.y + t.height > fr.height + 0.5) issues.push("outside frame: " + t.characters);
    const inBoxText = d.nodes.some(n => t.x >= n.x - 0.5 && t.x <= n.x + n.w && t.y >= n.y - 0.5 && t.y <= n.y + n.h);
    if (!inBoxText && t.y < d.body && buses.some(xm => t.x < xm + 1.5 && t.x + t.width > xm - 1.5)) issues.push(`bus crosses text: ${t.characters}`);
  }
  for (let i = 0; i < texts.length; i++) for (let j = i + 1; j < texts.length; j++) {
    const a = texts[i], b = texts[j];
    if (a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height) issues.push(`overlap: "${a.characters}" / "${b.characters}"`);
  }
  out.push({option: d.option, frame: fr.id, w: fr.width, h: fr.height, texts: texts.length, issues});
}
return out;
"""

code = JS.replace("__DATA__", json.dumps(D, ensure_ascii=False, separators=(",", ":")))
path = SRC.replace("diagrams.json", "figma_" + "_".join(names) + ".js")
open(path, "w", encoding="utf-8").write(code)
print(path, len(code), "chars")
