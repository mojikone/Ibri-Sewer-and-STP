
const D = [{"option":"S5","title":"four STPs at O-1, O-2, O-3, O-7","width":1660,"body":1087.0,"height":1197.0,"nodes":[{"id":"O22","kind":"sub","zone":"O1","x":560,"y":40.0,"w":128,"h":50,"lines":["O22"]},{"id":"O23","kind":"sub","zone":"O1","x":560,"y":102.0,"w":128,"h":50,"lines":["O23"]},{"id":"O21","kind":"sub","zone":"O1","x":820,"y":71.0,"w":128,"h":50,"lines":["O21"]},{"id":"O2","kind":"sub","zone":"O1","x":820,"y":164.0,"w":128,"h":50,"lines":["O2"]},{"id":"O24","kind":"sub","zone":"O1","x":820,"y":226.0,"w":128,"h":50,"lines":["O24"]},{"id":"O15","kind":"sub","zone":"O1","x":820,"y":288.0,"w":128,"h":50,"lines":["O15"]},{"id":"O1","kind":"sub","zone":"O1","x":1080,"y":187.25,"w":128,"h":50,"lines":["O1"]},{"id":"O19","kind":"sub","zone":"O1","x":820,"y":350.0,"w":128,"h":50,"lines":["O19"]},{"id":"O20","kind":"sub","zone":"O1","x":820,"y":412.0,"w":128,"h":50,"lines":["O20"]},{"id":"O16","kind":"sub","zone":"O1","x":1080,"y":381.0,"w":128,"h":50,"lines":["O16"]},{"id":"O17","kind":"sub","zone":"O1","x":1080,"y":474.0,"w":128,"h":50,"lines":["O17"]},{"id":"O18","kind":"sub","zone":"O1","x":1080,"y":536.0,"w":128,"h":50,"lines":["O18"]},{"id":"P:O1","kind":"plant","zone":"O1","x":1340,"y":359.5625,"w":280,"h":120,"lines":["STP O1","2030 → 2070","average 13,684 → 25,915 m³/d","peak 365 → 668 L/s",""]},{"id":"O13","kind":"sub","zone":"O9","x":40,"y":638.0,"w":128,"h":50,"lines":["O13"]},{"id":"O12","kind":"sub","zone":"O9","x":300,"y":638.0,"w":128,"h":50,"lines":["O12"]},{"id":"O11","kind":"sub","zone":"O9","x":560,"y":638.0,"w":128,"h":50,"lines":["O11"]},{"id":"O10","kind":"sub","zone":"O9","x":820,"y":638.0,"w":128,"h":50,"lines":["O10"]},{"id":"O14","kind":"sub","zone":"O9","x":820,"y":700.0,"w":128,"h":50,"lines":["O14"]},{"id":"O9","kind":"sub","zone":"O9","x":1080,"y":669.0,"w":128,"h":50,"lines":["O9"]},{"id":"P:O9","kind":"plant","zone":"O9","x":1340,"y":634.0,"w":280,"h":120,"lines":["STP O9","2030 → 2070","average 2,490 → 15,640 m³/d","peak 71 → 382 L/s",""]},{"id":"O7","kind":"sub","zone":"O4","x":300,"y":801.9999999999999,"w":128,"h":50,"lines":["O7"]},{"id":"O6","kind":"sub","zone":"O4","x":560,"y":801.9999999999999,"w":128,"h":50,"lines":["O6"]},{"id":"O8","kind":"sub","zone":"O4","x":560,"y":863.9999999999999,"w":128,"h":50,"lines":["O8"]},{"id":"O5","kind":"sub","zone":"O4","x":820,"y":832.9999999999999,"w":128,"h":50,"lines":["O5"]},{"id":"O4","kind":"sub","zone":"O4","x":1080,"y":832.9999999999999,"w":128,"h":50,"lines":["O4"]},{"id":"P:O4","kind":"plant","zone":"O4","x":1340,"y":797.9999999999999,"w":280,"h":120,"lines":["STP O4","2030 → 2070","average 3,571 → 7,935 m³/d","peak 106 → 222 L/s",""]},{"id":"O3","kind":"sub","zone":"O3","x":1080,"y":965.9999999999999,"w":128,"h":50,"lines":["O3"]},{"id":"P:O3","kind":"plant","zone":"O3","x":1340,"y":930.9999999999999,"w":280,"h":120,"lines":["STP O3","2030 → 2070","average 5,011 → 10,966 m³/d","peak 131 → 263 L/s",""]}],"edges":[{"src":"O7","dst":"O6","kind":"pumped","label":"47 L/s"},{"src":"O6","dst":"O5","kind":"pumped","label":"71 L/s"},{"src":"O8","dst":"O5","kind":"pumped","label":"20 L/s"},{"src":"O5","dst":"O4","kind":"pumped","label":"122 L/s"},{"src":"O2","dst":"O1","kind":"pumped","label":"150 L/s"},{"src":"O23","dst":"O21","kind":"pumped","label":"5 L/s"},{"src":"O22","dst":"O21","kind":"pumped","label":"11 L/s"},{"src":"O21","dst":"O1","kind":"pumped","label":"121 L/s"},{"src":"O24","dst":"O1","kind":"pumped","label":"55 L/s"},{"src":"O13","dst":"O12","kind":"pumped","label":"2 L/s"},{"src":"O12","dst":"O11","kind":"pumped","label":"42 L/s"},{"src":"O11","dst":"O10","kind":"pumped","label":"64 L/s"},{"src":"O10","dst":"O9","kind":"pumped","label":"100 L/s"},{"src":"O14","dst":"O9","kind":"pumped","label":"12 L/s"},{"src":"O15","dst":"O1","kind":"pumped","label":"35 L/s"},{"src":"O20","dst":"O16","kind":"pumped","label":"11 L/s"},{"src":"O19","dst":"O16","kind":"pumped","label":"12 L/s"},{"src":"O16","dst":"P:O1","kind":"pumped","label":"58 L/s"},{"src":"O17","dst":"P:O1","kind":"pumped","label":"15 L/s"},{"src":"O18","dst":"P:O1","kind":"pumped","label":"12 L/s"},{"src":"O4","dst":"P:O4","kind":"gravity","label":"gravity"},{"src":"O3","dst":"P:O3","kind":"gravity","label":"gravity"},{"src":"O9","dst":"P:O9","kind":"gravity","label":"gravity"},{"src":"O1","dst":"P:O1","kind":"gravity","label":"gravity"}],"font":{"name":20,"old":16,"edge":17,"plant_title":19,"plant":16,"legend":16},"box":{"w":128,"h":50,"col":260},"y0":6400},{"option":"S6","title":"six STPs at O-1, O-2, O-3, O-7, O-8, O-14","width":1660,"body":1228.9999999999998,"height":1338.9999999999998,"nodes":[{"id":"O13","kind":"sub","zone":"O9","x":40,"y":40.0,"w":128,"h":50,"lines":["O13"]},{"id":"O12","kind":"sub","zone":"O9","x":300,"y":40.0,"w":128,"h":50,"lines":["O12"]},{"id":"O11","kind":"sub","zone":"O9","x":560,"y":40.0,"w":128,"h":50,"lines":["O11"]},{"id":"O10","kind":"sub","zone":"O9","x":820,"y":40.0,"w":128,"h":50,"lines":["O10"]},{"id":"O14","kind":"sub","zone":"O9","x":820,"y":102.0,"w":128,"h":50,"lines":["O14"]},{"id":"O9","kind":"sub","zone":"O9","x":1080,"y":71.0,"w":128,"h":50,"lines":["O9"]},{"id":"P:O9","kind":"plant","zone":"O9","x":1340,"y":36.0,"w":280,"h":120,"lines":["STP O9","2030 → 2070","average 2,490 → 15,640 m³/d","peak 71 → 382 L/s",""]},{"id":"O7","kind":"sub","zone":"O4","x":300,"y":204.0,"w":128,"h":50,"lines":["O7"]},{"id":"O6","kind":"sub","zone":"O4","x":560,"y":204.0,"w":128,"h":50,"lines":["O6"]},{"id":"O8","kind":"sub","zone":"O4","x":560,"y":266.0,"w":128,"h":50,"lines":["O8"]},{"id":"O5","kind":"sub","zone":"O4","x":820,"y":235.0,"w":128,"h":50,"lines":["O5"]},{"id":"O4","kind":"sub","zone":"O4","x":1080,"y":235.0,"w":128,"h":50,"lines":["O4"]},{"id":"P:O4","kind":"plant","zone":"O4","x":1340,"y":200.0,"w":280,"h":120,"lines":["STP O4","2030 → 2070","average 3,571 → 7,935 m³/d","peak 106 → 222 L/s",""]},{"id":"O2","kind":"sub","zone":"O1","x":820,"y":368.0,"w":128,"h":50,"lines":["O2"]},{"id":"O21","kind":"sub","zone":"O1","x":820,"y":430.0,"w":128,"h":50,"lines":["O21"]},{"id":"O24","kind":"sub","zone":"O1","x":820,"y":492.0,"w":128,"h":50,"lines":["O24"]},{"id":"O15","kind":"sub","zone":"O1","x":820,"y":553.9999999999999,"w":128,"h":50,"lines":["O15"]},{"id":"O1","kind":"sub","zone":"O1","x":1080,"y":461.0,"w":128,"h":50,"lines":["O1"]},{"id":"P:O1","kind":"plant","zone":"O1","x":1340,"y":426.0,"w":280,"h":120,"lines":["STP O1","2030 → 2070","average 12,950 → 22,867 m³/d","peak 339 → 567 L/s",""]},{"id":"O19","kind":"sub","zone":"O16","x":820,"y":655.9999999999999,"w":128,"h":50,"lines":["O19"]},{"id":"O20","kind":"sub","zone":"O16","x":820,"y":717.9999999999999,"w":128,"h":50,"lines":["O20"]},{"id":"O16","kind":"sub","zone":"O16","x":1080,"y":686.9999999999999,"w":128,"h":50,"lines":["O16"]},{"id":"O17","kind":"sub","zone":"O16","x":1080,"y":779.9999999999999,"w":128,"h":50,"lines":["O17"]},{"id":"O18","kind":"sub","zone":"O16","x":1080,"y":841.9999999999999,"w":128,"h":50,"lines":["O18"]},{"id":"P:O16","kind":"plant","zone":"O16","x":1340,"y":734.6666666666665,"w":280,"h":120,"lines":["STP O16","2030 → 2070","average 657 → 2,602 m³/d","peak 24 → 85 L/s",""]},{"id":"O22","kind":"sub","zone":"O22","x":1080,"y":943.9999999999999,"w":128,"h":50,"lines":["O22"]},{"id":"O23","kind":"sub","zone":"O22","x":1080,"y":1005.9999999999999,"w":128,"h":50,"lines":["O23"]},{"id":"P:O22","kind":"plant","zone":"O22","x":1340,"y":939.9999999999999,"w":280,"h":120,"lines":["STP O22","2030 → 2070","average 77 → 446 m³/d","peak 2 → 16 L/s",""]},{"id":"O3","kind":"sub","zone":"O3","x":1080,"y":1107.9999999999998,"w":128,"h":50,"lines":["O3"]},{"id":"P:O3","kind":"plant","zone":"O3","x":1340,"y":1072.9999999999998,"w":280,"h":120,"lines":["STP O3","2030 → 2070","average 5,011 → 10,966 m³/d","peak 131 → 263 L/s",""]}],"edges":[{"src":"O7","dst":"O6","kind":"pumped","label":"47 L/s"},{"src":"O6","dst":"O5","kind":"pumped","label":"71 L/s"},{"src":"O8","dst":"O5","kind":"pumped","label":"20 L/s"},{"src":"O5","dst":"O4","kind":"pumped","label":"122 L/s"},{"src":"O2","dst":"O1","kind":"pumped","label":"150 L/s"},{"src":"O21","dst":"O1","kind":"pumped","label":"105 L/s"},{"src":"O24","dst":"O1","kind":"pumped","label":"55 L/s"},{"src":"O13","dst":"O12","kind":"pumped","label":"2 L/s"},{"src":"O12","dst":"O11","kind":"pumped","label":"42 L/s"},{"src":"O11","dst":"O10","kind":"pumped","label":"64 L/s"},{"src":"O10","dst":"O9","kind":"pumped","label":"100 L/s"},{"src":"O14","dst":"O9","kind":"pumped","label":"12 L/s"},{"src":"O15","dst":"O1","kind":"pumped","label":"35 L/s"},{"src":"O20","dst":"O16","kind":"pumped","label":"11 L/s"},{"src":"O19","dst":"O16","kind":"pumped","label":"12 L/s"},{"src":"O17","dst":"P:O16","kind":"pumped","label":"15 L/s"},{"src":"O18","dst":"P:O16","kind":"pumped","label":"12 L/s"},{"src":"O23","dst":"P:O22","kind":"pumped","label":"5 L/s"},{"src":"O4","dst":"P:O4","kind":"gravity","label":"gravity"},{"src":"O3","dst":"P:O3","kind":"gravity","label":"gravity"},{"src":"O9","dst":"P:O9","kind":"gravity","label":"gravity"},{"src":"O1","dst":"P:O1","kind":"gravity","label":"gravity"},{"src":"O16","dst":"P:O16","kind":"gravity","label":"gravity"},{"src":"O22","dst":"P:O22","kind":"gravity","label":"gravity"}],"font":{"name":20,"old":16,"edge":17,"plant_title":19,"plant":16,"legend":16},"box":{"w":128,"h":50,"col":260},"y0":8000},{"option":"S7","title":"three STPs at O-1, O-8, O-14","width":2180,"body":953.9999999999999,"height":1064.0,"nodes":[{"id":"O7","kind":"sub","zone":"O1","x":40,"y":40.0,"w":128,"h":50,"lines":["O7"]},{"id":"O6","kind":"sub","zone":"O1","x":300,"y":40.0,"w":128,"h":50,"lines":["O6"]},{"id":"O8","kind":"sub","zone":"O1","x":300,"y":102.0,"w":128,"h":50,"lines":["O8"]},{"id":"O5","kind":"sub","zone":"O1","x":560,"y":71.0,"w":128,"h":50,"lines":["O5"]},{"id":"O4","kind":"sub","zone":"O1","x":820,"y":71.0,"w":128,"h":50,"lines":["O4"]},{"id":"O3","kind":"sub","zone":"O1","x":1080,"y":71.0,"w":128,"h":50,"lines":["O3"]},{"id":"O2","kind":"sub","zone":"O1","x":1340,"y":71.0,"w":128,"h":50,"lines":["O2"]},{"id":"O13","kind":"sub","zone":"O1","x":300,"y":164.0,"w":128,"h":50,"lines":["O13"]},{"id":"O12","kind":"sub","zone":"O1","x":560,"y":164.0,"w":128,"h":50,"lines":["O12"]},{"id":"O11","kind":"sub","zone":"O1","x":820,"y":164.0,"w":128,"h":50,"lines":["O11"]},{"id":"O10","kind":"sub","zone":"O1","x":1080,"y":164.0,"w":128,"h":50,"lines":["O10"]},{"id":"O14","kind":"sub","zone":"O1","x":1080,"y":226.0,"w":128,"h":50,"lines":["O14"]},{"id":"O9","kind":"sub","zone":"O1","x":1340,"y":195.0,"w":128,"h":50,"lines":["O9"]},{"id":"O21","kind":"sub","zone":"O1","x":1340,"y":288.0,"w":128,"h":50,"lines":["O21"]},{"id":"O24","kind":"sub","zone":"O1","x":1340,"y":350.0,"w":128,"h":50,"lines":["O24"]},{"id":"O15","kind":"sub","zone":"O1","x":1340,"y":412.0,"w":128,"h":50,"lines":["O15"]},{"id":"O1","kind":"sub","zone":"O1","x":1600,"y":263.20000000000005,"w":128,"h":50,"lines":["O1"]},{"id":"P:O1","kind":"plant","zone":"O1","x":1860,"y":228.20000000000005,"w":280,"h":120,"lines":["STP O1","2030 → 2070","average 24,021 → 57,408 m³/d","peak 648 → 1,435 L/s",""]},{"id":"O19","kind":"sub","zone":"O16","x":1340,"y":514.0,"w":128,"h":50,"lines":["O19"]},{"id":"O20","kind":"sub","zone":"O16","x":1340,"y":576.0,"w":128,"h":50,"lines":["O20"]},{"id":"O16","kind":"sub","zone":"O16","x":1600,"y":545.0,"w":128,"h":50,"lines":["O16"]},{"id":"O17","kind":"sub","zone":"O16","x":1600,"y":638.0,"w":128,"h":50,"lines":["O17"]},{"id":"O18","kind":"sub","zone":"O16","x":1600,"y":700.0,"w":128,"h":50,"lines":["O18"]},{"id":"P:O16","kind":"plant","zone":"O16","x":1860,"y":592.6666666666666,"w":280,"h":120,"lines":["STP O16","2030 → 2070","average 657 → 2,602 m³/d","peak 24 → 85 L/s",""]},{"id":"O22","kind":"sub","zone":"O22","x":1600,"y":801.9999999999999,"w":128,"h":50,"lines":["O22"]},{"id":"O23","kind":"sub","zone":"O22","x":1600,"y":863.9999999999999,"w":128,"h":50,"lines":["O23"]},{"id":"P:O22","kind":"plant","zone":"O22","x":1860,"y":797.9999999999999,"w":280,"h":120,"lines":["STP O22","2030 → 2070","average 77 → 446 m³/d","peak 2 → 16 L/s",""]}],"edges":[{"src":"O7","dst":"O6","kind":"pumped","label":"47 L/s"},{"src":"O6","dst":"O5","kind":"pumped","label":"71 L/s"},{"src":"O8","dst":"O5","kind":"pumped","label":"20 L/s"},{"src":"O5","dst":"O4","kind":"pumped","label":"122 L/s"},{"src":"O4","dst":"O3","kind":"pumped","label":"222 L/s"},{"src":"O3","dst":"O2","kind":"pumped","label":"486 L/s"},{"src":"O2","dst":"O1","kind":"pumped","label":"636 L/s"},{"src":"O21","dst":"O1","kind":"pumped","label":"105 L/s"},{"src":"O24","dst":"O1","kind":"pumped","label":"55 L/s"},{"src":"O13","dst":"O12","kind":"pumped","label":"2 L/s"},{"src":"O12","dst":"O11","kind":"pumped","label":"42 L/s"},{"src":"O11","dst":"O10","kind":"pumped","label":"64 L/s"},{"src":"O10","dst":"O9","kind":"pumped","label":"100 L/s"},{"src":"O14","dst":"O9","kind":"pumped","label":"12 L/s"},{"src":"O9","dst":"O1","kind":"pumped","label":"382 L/s"},{"src":"O15","dst":"O1","kind":"pumped","label":"35 L/s"},{"src":"O20","dst":"O16","kind":"pumped","label":"11 L/s"},{"src":"O19","dst":"O16","kind":"pumped","label":"12 L/s"},{"src":"O17","dst":"P:O16","kind":"pumped","label":"15 L/s"},{"src":"O18","dst":"P:O16","kind":"pumped","label":"12 L/s"},{"src":"O23","dst":"P:O22","kind":"pumped","label":"5 L/s"},{"src":"O16","dst":"P:O16","kind":"gravity","label":"gravity"},{"src":"O1","dst":"P:O1","kind":"gravity","label":"gravity"},{"src":"O22","dst":"P:O22","kind":"gravity","label":"gravity"}],"font":{"name":20,"old":16,"edge":17,"plant_title":19,"plant":16,"legend":16},"box":{"w":128,"h":50,"col":260},"y0":9600}];
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
      if (n.lines[4]) inBox(n, n.lines[4], 96, F.plant, {color: "#FFFFFF"});
    } else {
      inBox(n, n.lines[0], 13, F.name, {bold: true});     // the current name only
    }
  }
  // legend, left to right, wrapping when the row is full
  const plants = d.nodes.filter(n => n.kind === "plant"), zc = hex(ZONE[plants[0].zone] || "#555555");
  const L = F.legend, items = [
    {kind: "box", s: "Subnetwork, named after its outfall" + (plants.length > 1 ? ", coloured by its STP" : "")},
    {kind: "pumped", s: "Pumping station at the outfall and its rising main, 2070 peak flow"},
    {kind: "gravity", s: "Gravity: the STP sits at this subnetwork's own outfall"},
    {kind: "plant", s: "STP: flows 2030 → 2070 and the depth of the incoming sewer"}];
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
