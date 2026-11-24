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
