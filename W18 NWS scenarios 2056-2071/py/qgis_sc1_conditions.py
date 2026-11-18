"""W18 (engineer, 2026-11-18): the four SC1 conditions, from the re-lay of the SewerGEMS design R5
(py/split_deep_subnetworks.py, results/sc1_conditions/), added to the QGIS project of the plot flows that the engineer
was sent (qgis/W18_plot_flows.qgz), with a saved print layout and an exported map for each:
  C0 as designed: pipes by velocity at the 2031 peak (graduated, under 0.75 m/s in reds), width by size;
  C1-C3 steepened to reach 0.75 m/s at the 2031 peak with gradients up to 0.50 / 0.75 / 1.00 % (one gradient per
     street run) and split where a subnetwork stays deeper than 12 m: pipes steepened by gradient range, pipes above
     DN200 that still do not reach 0.75 m/s, pipes deeper than 12 m, the new rising mains;
  every map: pipes over 3.0 m/s at the 2056 design flow (PAM-GUD-203 p27) and the outfalls labelled with name and depth.
Frame and machinery as the W17 maps (gis/template_report_A3.qpt, gis/make_w17_project.py): data box bottom right,
legend bottom left, Google satellite hybrid at 30 % rendered for each map's extent (the layout exporter crashes on
web tiles; the saved layouts keep the live layer).
Run after py/qgis_plot_flows_project.py (which rebuilds the project from scratch):
    & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" qgis_sc1_conditions.py [--no-render]
Writes qgis/W18_plot_flows.qgz and results/sc1_conditions/maps/SC1_C#_*.png."""
import json, os, sys, tempfile
sys.stdout.reconfigure(line_buffering=True)
from qgis.core import (Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemLabel, QgsLayoutExporter, QgsLayoutSize, QgsLayoutPoint, QgsTextFormat,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange,
                       QgsSingleSymbolRenderer, QgsLineSymbol, QgsMarkerSymbol, QgsProperty, QgsSymbolLayer,
                       QgsRectangle, QgsLayerTreeGroup)
from qgis.PyQt.QtGui import QColor, QFont

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W18, "gis"))
import make_w17_project as M                          # the W17 map frame: clone, fill_box, clear_extent, background

PROJECT = os.path.join(W18, "qgis", "W18_plot_flows.qgz")
RES = os.path.join(W18, "results", "sc1_conditions")
MAPS = os.path.join(RES, "maps")
TAG = "SC1-2056"
GROUP = "SC1 sewer conditions (re-lay of SewerGEMS R5, design year 2056)"
SUBTITLE = "Ibri Sewer, TE Networks and STP — SC1 working map, re-lay of the SewerGEMS design | Renardet 2621"
RENDER = "--no-render" not in sys.argv
CONDS = [("C0_as_designed", "C0", "As designed", None),
         ("C1_limit_0.50pc", "C1", "Steepened, gradient up to 0.50 %", 0.50),
         ("C2_limit_0.75pc", "C2", "Steepened, gradient up to 0.75 %", 0.75),
         ("C3_limit_1.00pc", "C3", "Steepened, gradient up to 1.00 %", 1.00)]
WIDTH = ('CASE WHEN "dn_mm" >= 1400 THEN 2.0 WHEN "dn_mm" >= 1000 THEN 1.6 WHEN "dn_mm" >= 630 THEN 1.2 '
         'WHEN "dn_mm" >= 400 THEN 0.85 WHEN "dn_mm" > 200 THEN 0.55 ELSE 0.2 END')
SIZES = [(200, 200, "DN200", 0.2), (201, 399, "DN250 to 355", 0.55), (400, 629, "DN400 to 560", 0.85),
         (630, 999, "DN630 to 900", 1.2), (1000, 1399, "DN1000 to 1200", 1.6), (1400, 9999, "DN1400 and over", 2.0)]
VEL = [(0.0, 0.15, "#67000d", "under 0.15"), (0.15, 0.30, "#cb181d", "0.15 to 0.30"), (0.30, 0.45, "#fb6a4a", "0.30 to 0.45"),
       (0.45, 0.60, "#fd8d3c", "0.45 to 0.60"), (0.60, 0.75, "#fed976", "0.60 to 0.75"),
       (0.75, 3.0, "#1a9850", "0.75 to 3.0 (self-cleansing)"), (3.0, 99.0, "#e7298a", "over 3.0")]
CLASSES = [("DN200 (not steepened)", "#9e9e9e", "DN200, not steepened (rule: above DN200 only)"),
           ("Above DN200, 0.75 m/s as laid", "#1a9850", "Above DN200, reaches 0.75 m/s as laid"),
           ("Steepened up to 0.30 %", "#fdd49e", "Steepened to up to 0.30 %"),
           ("Steepened 0.30 to 0.50 %", "#fc8d59", "Steepened to 0.30 to 0.50 %"),
           ("Steepened 0.50 to 0.75 %", "#d7301f", "Steepened to 0.50 to 0.75 %"),
           ("Steepened 0.75 to 1.00 %", "#7f0000", "Steepened to 0.75 to 1.00 %"),
           ("Above DN200, under 0.75 m/s", "#7b3294", "Above DN200, does not reach 0.75 m/s"),
           ("Gravity join (was a rising main)", "#00a651", "Gravity join (was a rising main)")]
OUTFALL = [("Plant inlet", "square", "#1F3B63", 4.2), ("Existing station", "circle", "#a61b1b", 2.6),
           ("New station", "triangle", "#1f3fff", 3.4), ("Joined by gravity", "circle", "#00a651", 2.2)]


def sym_line(colour, width=0.3, dd=True, style="solid", alpha=1.0):
    s = QgsLineSymbol.createSimple({"color": colour, "width": str(width), "capstyle": "round", "joinstyle": "round",
                                    "line_style": style})
    if dd: s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression(WIDTH))
    s.setOpacity(alpha)
    return s


def lyr(gpkg, layer, name, subset=""):
    l = QgsVectorLayer(f"{gpkg}|layername={layer}", name, "ogr")
    if not l.isValid(): return None
    if subset: l.setSubsetString(subset)
    return l


def size_legend():
    l = QgsVectorLayer("LineString?crs=EPSG:32640&field=dn_mm:integer", "Pipe size (line width)", "memory")
    l.setRenderer(QgsGraduatedSymbolRenderer("dn_mm", [QgsRendererRange(lo, hi, sym_line("#555555", w, dd=False), lab)
                                                       for lo, hi, lab, w in SIZES]))
    return l


def present(l, field):
    """The values a layer holds in a field: the legend lists only classes that are on the map."""
    return set(l.uniqueValues(l.fields().indexOf(field)))


def style_outfalls(l):
    have = present(l, "kind")
    cats = [QgsRendererCategory(k, QgsMarkerSymbol.createSimple({"name": shp, "color": c, "outline_color": "#ffffff",
                                                                 "outline_width": "0.35", "size": str(sz)}), k)
            for k, shp, c, sz in OUTFALL if k in have]
    l.setRenderer(QgsCategorizedSymbolRenderer("kind", cats))
    M.label(l, '"map_label"', size=6.0, colour="#1a1a1a", bold=True, priority=10, dist=0.8)


def make_map(proj, google, name, title, stack, legend_layers, ext, rows, out_png, test_layers):
    """As make_w17_project.make_map, with this map set's subtitle, the background at 30 % and no copy to a report."""
    lay = M.clone(proj, name)
    mapitem = legend = None
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap):
            it.setLayers(stack + [google]); it.setKeepLayerSet(True); it.zoomToExtent(ext); mapitem = it
        elif isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"):
                it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(230, 4.5, M.UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, M.UNIT_MM))
            elif t and not t.startswith("N"):
                it.setText(title); it.attemptResize(QgsLayoutSize(260, 6.5, M.UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, M.UNIT_MM))
        elif isinstance(it, QgsLayoutItemLegend):
            legend = it
    box = M.fill_box(lay, rows, width=92.0)
    if legend is not None:
        legend.setLinkedMap(mapitem); legend.setAutoUpdateModel(False)
        legend.setBackgroundEnabled(True); legend.setBackgroundColor(QColor(255, 255, 255, M.LEGEND_ALPHA))
        legend.setWrapString("~")
        grp = legend.model().rootGroup()
        for ch in list(grp.children()): grp.removeChildNode(ch)
        for l, show_title in legend_layers:
            node = grp.addLayer(l)
            if not show_title: node.setCustomProperty("legend/title-style", "hidden")
        legend.setTitle(""); legend.setResizeToContents(True); legend.adjustBoxSize()
        tmp = QgsLayoutExporter(lay); ts = QgsLayoutExporter.ImageExportSettings(); ts.dpi = 25
        mapitem.setLayers(stack)
        tmp.exportToImage(os.path.join(tempfile.gettempdir(), "w18_legend_probe.png"), ts)
        sz = legend.sizeWithUnits(); mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
        legend.attemptMove(QgsLayoutPoint(mp.x() + 3.0, mp.y() + ms.height() - sz.height() - 3.0, M.UNIT_MM))
        print(f"      legend {sz.width():.1f} x {sz.height():.1f} mm")
    boxes = ([(legend, "left")] if legend is not None else []) + ([(box, "right")] if box is not None else [])
    mapitem.zoomToExtent(M.clear_extent(mapitem, boxes, ext, test_layers))
    credit = QgsLayoutItemLabel(lay); credit.setText(M.CREDIT)
    tf = QgsTextFormat(); tf.setFont(QFont("Arial")); tf.setSize(5.0); tf.setColor(QColor("#4a4a4a")); credit.setTextFormat(tf)
    lay.addLayoutItem(credit); credit.attemptResize(QgsLayoutSize(40, 3.5, M.UNIT_MM))
    mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
    cx = (legend.positionWithUnits().x() + legend.sizeWithUnits().width() + 2.0) if legend is not None else mp.x() + 1.5
    credit.attemptMove(QgsLayoutPoint(cx, mp.y() + ms.height() - 4.2, M.UNIT_MM))
    if RENDER:
        bg = M.google_background(proj, google, mapitem, name.replace(" ", "_")); bg.setOpacity(0.3)
        mapitem.setLayers(stack + [bg])
        exp = QgsLayoutExporter(lay); s = QgsLayoutExporter.ImageExportSettings(); s.dpi = M.DPI
        res = exp.exportToImage(out_png, s)
        print("   ", os.path.basename(out_png), "ok" if res == QgsLayoutExporter.Success else f"FAILED {res}")
        proj.removeMapLayer(bg.id())
    mapitem.setLayers(stack + [google])


def fmt(v, d=1): return f"{v:,.{d}f}"


def build():
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); assert proj.read(PROJECT), PROJECT
    root = proj.layerTreeRoot()
    old = root.findGroup(GROUP)
    if old is not None:
        for l in old.findLayers(): proj.removeMapLayer(l.layerId())
        root.removeChildNode(old)
    for lay in list(proj.layoutManager().layouts()):
        if lay.name().startswith("SC1 C"): proj.layoutManager().removeLayout(lay)
    google = next(l for l in proj.mapLayers().values() if l.name().startswith("Google"))
    settle = next(l for l in proj.mapLayers().values() if l.name() == "Settlement boundary")
    os.makedirs(MAPS, exist_ok=True)
    top = root.insertGroup(0, GROUP)

    def add(group, l, visible=True):
        if l is None: return None
        proj.addMapLayer(l, False); node = group.addLayer(l); node.setItemVisibilityChecked(visible); node.setExpanded(False)
        return l

    for i, (folder, code, cname, limit) in enumerate(CONDS):
        gpkg = os.path.join(RES, folder, f"split_{TAG}.gpkg")
        S = json.load(open(os.path.join(RES, folder, f"summary_{TAG}.json")))
        g = top.addGroup(f"{code} {cname}"); g.setExpanded(False)
        outf = lyr(gpkg, "outfalls", "Outfall / pumping station: name and depth"); style_outfalls(outf)
        over3 = lyr(gpkg, "pipes", "Pipe over 3.0 m/s at the 2056 peak", '"over3" = 1')
        over3.setRenderer(QgsSingleSymbolRenderer(sym_line("#e7298a", 1.8, dd=False, alpha=0.8)))
        if limit is None:                                   # C0: velocity at the 2031 peak
            pipes = lyr(gpkg, "pipes", "Velocity at the 2031 peak, m/s")
            pipes.setRenderer(QgsGraduatedSymbolRenderer("v2031_ms", [QgsRendererRange(lo, hi, sym_line(c), lab) for lo, hi, c, lab in VEL]))
            deep = lyr(gpkg, "pipes", "Pipe deeper than 12 m", '"deep12" = 1')
            deep.setRenderer(QgsSingleSymbolRenderer(sym_line("#00bcd4", 1.7, dd=False, alpha=0.55)))
            mhd = lyr(gpkg, "manholes_deep", "Manhole deeper than 12 m (depth)")
            add(g, outf); add(g, over3); add(g, pipes); add(g, deep, False)
            title = "SC1 C0, as designed (2056): pipe velocity at the 2031 peak"
            rows = [("Pipes", f"{fmt(S['km_total'], 0)} km"),
                    ("DN200 under 0.75 m/s (2031 peak)", f"{fmt(S['km_dn200_under075'])} of {fmt(S['km_dn200'])} km"),
                    ("Above DN200 under 0.75 m/s", f"{fmt(S['km_big_under075'])} of {fmt(S['km_big'])} km ({100 * S['km_big_under075'] / S['km_big']:.0f} %)"),
                    ("Highest velocity, 2056 peak", f"{S['v2056_max']:.2f} m/s"),
                    ("Pipes over 3.0 m/s (G203 p27)", f"{S['n_over3']}" if S["n_over3"] else "none"),
                    ("Pumping stations", f"{S['stations']}"),
                    ("Outfalls deeper than 12 m", (f"{len(S['outfalls_over12'])} (deepest " + max(
                        (f"{o['name']} {o['depth_m']:.1f} m" for o in S["outfalls_over12"]), key=lambda s: float(s.split()[1])) + ")")
                        if S["outfalls_over12"] else "none"),
                    ("Manholes deeper than 12 m", f"{S['mh_over12']} (deepest {S['mh_deepest']:.1f} m)")]
            stack = [outf, over3, pipes, settle]
            legend = [(outf, False), (pipes, True), (size_legend(), True), (over3, False), (settle, False)]
        else:
            pipes = lyr(gpkg, "pipes", "Pipes")
            have = present(pipes, "map_class")
            pipes.setRenderer(QgsCategorizedSymbolRenderer("map_class", [
                QgsRendererCategory(v, sym_line(c, style="dash" if v.startswith("Gravity join") else "solid"), lab)
                for v, c, lab in CLASSES if v in have]))
            assert have <= {v for v, _, _ in CLASSES}, have - {v for v, _, _ in CLASSES}
            deep = lyr(gpkg, "pipes", "Pipe deeper than 12 m", '"deep12" = 1')
            deep.setRenderer(QgsSingleSymbolRenderer(sym_line("#00bcd4", 1.7, dd=False, alpha=0.55)))
            rmn = lyr(gpkg, "rising_mains_new", "Rising main of a new station")
            if rmn is not None: M.style_rising(rmn, 0.6); rmn.setName("Rising main of a new station")
            before = lyr(gpkg, "deep_before_split", "Deeper than 12 m if steepened and not split")
            if before is not None: before.setRenderer(QgsSingleSymbolRenderer(sym_line("#000000", 0.9, dd=False, style="dot")))
            mhd = lyr(gpkg, "manholes_deep", "Manhole deeper than 12 m (depth)")
            add(g, outf); add(g, rmn); add(g, over3); add(g, pipes); add(g, deep); add(g, before, False)
            title = f"SC1 {code}: steepened for 0.75 m/s at 2031, gradient up to {limit:.2f} %, split below 12 m"
            band_rows = [(f"   to {b}", f"{fmt(v)} km") for b, v in S["km_by_band"].items() if v > 0.05]
            rows = ([("Gradient limit", f"{limit:.2f} % (one gradient per street run)"),
                     ("Pipes above DN200", f"{fmt(S['km_big'])} km"),
                     ("Steepened", f"{fmt(S['km_steepened'])} km, {S['n_runs_steepened']} street runs")] + band_rows +
                    [("Still under 0.75 m/s (2031 peak)", f"{fmt(S['km_big_under075'])} km ({100 * S['km_big_under075'] / S['km_big']:.1f} %)"),
                     ("Pipes over 3.0 m/s (2056 peak)", f"{S['n_over3']}" if S["n_over3"] else f"none (highest {S['v2056_max']:.2f} m/s)"),
                     ("Pumping stations", f"{S['stations']} (as designed {S['stations_design']})"),
                     ("   new / existing joined by gravity", f"{S['stations_new']} / {S['joined']}"),
                     ("Manholes deeper than 12 m", f"{S['mh_over12']} (as designed {S['mh_over12_design']})"),
                     ("Deepest manhole", f"{S['mh_deepest']:.1f} m (a dip that comes back)")])
            stack = [x for x in (outf, rmn, over3, pipes, deep, settle) if x is not None]
            legend = [(outf, False), (pipes, False), (size_legend(), True), (deep, False)] + \
                     ([(rmn, False)] if rmn is not None else []) + [(over3, False), (settle, False)]
        if mhd is not None:
            mhd.setRenderer(QgsSingleSymbolRenderer(M.circle("#006d77", 1.4, width=0.2)))
            M.label(mhd, '"label" || \' \' || format_number("depth_m", 1) || \' m\'', size=5.0, colour="#006d77", priority=4, dist=0.5)
            add(g, mhd, False)
        root.findGroup(GROUP).findGroup(f"{code} {cname}").setItemVisibilityChecked(True)
        e = QgsRectangle(pipes.extent()); e.grow(max(e.width(), e.height()) * 0.02)
        make_map(proj, google, f"SC1 {code} {cname}", title, stack, legend, e, rows,
                 os.path.join(MAPS, f"SC1_{code}_{folder.split('_', 1)[1]}.png"), [pipes, outf])
    top.setIsMutuallyExclusive(True, 0)                      # one condition at a time, C0 first
    proj.writeEntryBool("Paths", "/Absolute", False)
    assert proj.write(PROJECT), PROJECT
    print("wrote", PROJECT, "|", len(proj.mapLayers()), "layers |", len(proj.layoutManager().layouts()), "layouts")
    app.exitQgis()


if __name__ == "__main__":
    build()
