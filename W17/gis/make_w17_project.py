"""Build the W17 QGIS project (network options S1-S7) from W17/Options 2026-10, with its print layouts cloned from
the report's map frame, and export the maps. Runs in the standalone QGIS python, so it never touches a QGIS window:

    & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" make_w17_project.py [S1 S2 ...]

Two maps per option, on the frame every R3 map uses (template_report_A3.qpt, extracted from stp2.qgz):
  network: pipes coloured by the plant they drain to, width by size; pumping stations labelled with the outfall depth,
           the pump head and the duty; rising mains dashed with an arrow to the receiving manhole or plant; the plants.
  depth:   pipes by depth band (green to navy up to 12 m, red beyond 12 m, the hard limit), width by size; manholes
           deeper than 9 m marked, those deeper than 12 m in red.
The data box of each map is filled from results/S#/S#_summary.json, the same file the report reads.
"""
import json, os, shutil, sys
sys.stdout.reconfigure(line_buffering=True)
# Qt's own Windows platform, not "offscreen": offscreen cannot see the Windows fonts and draws every glyph as a box
from qgis.core import (Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsRectangle, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemLabel, QgsLayoutExporter, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsLayoutFrame,
                       QgsLayoutItemManualTable, QgsTableCell, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsLineSymbol, QgsMarkerSymbol, QgsFillSymbol, QgsProperty, QgsSymbolLayer, QgsRuleBasedRenderer,
                       QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
                       QgsSingleSymbolRenderer, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer,
                       QgsGraduatedSymbolRenderer, QgsRendererRange, QgsLabelPlacementSettings)
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import QDomDocument

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W17, "py"))
from routing import SCENARIOS, OLD

F = os.path.join(W17, "Options 2026-10")
ST = os.path.join(F, "_styles")
PROJECT = os.path.join(F, "Ibri_W17_network_options.qgz")
TEMPLATE = os.path.join(HERE, "template_report_A3.qpt")
MAPS = os.path.join(F, "Maps")
IMG = os.path.join(W17, "report", "img")
GOOGLE = ("crs=EPSG:3857&format&http-header:referer=&type=xyz&url=https://www.google.cn/maps/vt?lyrs%3Ds@189%26gl%3Dcn"
          "%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0")
SUBTITLE = "Ibri Sewer, TE Networks and STP — Concept Design Report | Renardet 2621"   # as on every R3 map: no revision
NAVY = "#1F3B63"
UNIT_MM = QgsUnitTypes.LayoutMillimeters
ZONE_COLOUR = {"O1": "#2E75B6", "O4": "#C0504D", "O9": "#70AD47", "O3": "#7030A0", "O16": "#ED7D31", "O22": "#00A6D6"}
DEPTH = [("up to 3 m", "#a1d99b"), ("3 to 6 m", "#41ab5d"), ("6 to 9 m", "#4292c6"), ("9 to 12 m", "#08306b"),
         ("12 to 15 m", "#e31a1c"), ("over 15 m", "#67000d")]
WIDTH_EXPR = ('CASE WHEN "od_mm" >= 1400 THEN 2.0 WHEN "od_mm" >= 1000 THEN 1.6 WHEN "od_mm" >= 630 THEN 1.2 '
              'WHEN "od_mm" >= 400 THEN 0.85 WHEN "od_mm" >= 280 THEN 0.55 ELSE 0.28 END')
SIZE_CLASSES = [(0, 279, "OD 200 to 250", 0.28), (280, 399, "OD 280 to 355", 0.55), (400, 629, "OD 400 to 560", 0.85),
                (630, 999, "OD 630 to 900", 1.2), (1000, 1399, "OD 1000 to 1200", 1.6), (1400, 9999, "OD 1400 and over", 2.0)]
BOX_ANCHOR, ROW_MM = (286.3, 201.9), 5.6


def fmt(n, d=0):
    return f"{n:,.{d}f}"


def text_format(size, colour=NAVY, bold=False, buffer=0.8):
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b)
    return tf


def label(layer, expr, size=6.5, colour=NAVY, bold=False, overlap=True, priority=8):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    pal.setFormat(text_format(size, colour, bold)); pal.priority = priority
    if layer.geometryType() == Qgis.GeometryType.Point:
        pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; pal.dist = 1.2
    pal.multilineAlign = Qgis.LabelMultiLineAlignment.Left
    if overlap:
        ps = pal.placementSettings(); ps.setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired); pal.setPlacementSettings(ps)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal)); layer.setLabelsEnabled(True)


def line_symbol(colour, width=0.3, dd_width=True):
    s = QgsLineSymbol.createSimple({"color": colour, "width": str(width), "capstyle": "round", "joinstyle": "round"})
    if dd_width:
        s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression(WIDTH_EXPR))
    return s


def vec(path, name, layer=None):
    l = QgsVectorLayer(path + (f"|layername={layer}" if layer else ""), name, "ogr")
    if not l.isValid():
        print("   INVALID:", path, layer); return None
    return l


def style_pipes_zone(l, zones):
    cats = [QgsRendererCategory(z, line_symbol(ZONE_COLOUR.get(z, "#555555")), f"Drains to the STP at {z} ({OLD[z]})") for z in zones]
    l.setRenderer(QgsCategorizedSymbolRenderer("zone", cats))


def style_pipes_depth(l):
    cats = [QgsRendererCategory(b, line_symbol(c), f"Pipe {b} deep") for b, c in DEPTH]
    l.setRenderer(QgsCategorizedSymbolRenderer("depth_band", cats))


def size_legend_layer():
    """Not drawn: a legend entry that explains the line widths (data-defined widths do not show in a legend)."""
    l = QgsVectorLayer("LineString?crs=EPSG:32640&field=od_mm:integer", "Pipe size (outside diameter, mm)", "memory")
    rng = [QgsRendererRange(lo, hi, line_symbol("#555555", w, dd_width=False), lab) for lo, hi, lab, w in SIZE_CLASSES]
    l.setRenderer(QgsGraduatedSymbolRenderer("od_mm", rng))
    return l


def style_manholes_deep(l):
    root = QgsRuleBasedRenderer.Rule(None)
    for expr, colour, size, lab in (('"depth_m" > 12', "#e31a1c", "2.4", "Manhole deeper than 12 m"),
                                    ('"depth_m" > 9 AND "depth_m" <= 12', "#08306b", "1.5", "Manhole 9 to 12 m deep")):
        sym = QgsMarkerSymbol.createSimple({"name": "circle", "color": colour, "outline_color": "#ffffff", "outline_width": "0.25", "size": size})
        r = QgsRuleBasedRenderer.Rule(sym, 0, 0, expr, lab); root.appendChild(r)
    l.setRenderer(QgsRuleBasedRenderer(root))


def style_pumps(l):
    sym = QgsMarkerSymbol.createSimple({"name": "triangle", "color": "#a61b1b", "outline_color": "#ffffff", "outline_width": "0.35", "size": "3.6"})
    l.setRenderer(QgsSingleSymbolRenderer(sym))
    label(l, '"map_label"', size=5.6, colour="#5a0f0f", priority=10)


def style_plants(l):
    sym = QgsMarkerSymbol.createSimple({"name": "square", "color": NAVY, "outline_color": "#ffffff", "outline_width": "0.5", "size": "5.2"})
    l.setRenderer(QgsSingleSymbolRenderer(sym))
    label(l, '"map_label"', size=7.0, colour=NAVY, bold=True, priority=10)


def style_rising(l):
    sym = QgsLineSymbol.createSimple({"color": "#a61b1b", "width": "0.6", "line_style": "dash", "capstyle": "round"})
    head = QgsMarkerLineSymbolLayer(True); head.setPlacements(Qgis.MarkerLinePlacement.LastVertex)
    mk = QgsMarkerSymbol.createSimple({"name": "filled_arrowhead", "color": "#a61b1b", "outline_style": "no", "size": "3.2"})
    head.setSubSymbol(mk); sym.appendSymbolLayer(head)
    l.setRenderer(QgsSingleSymbolRenderer(sym))
    l.setName("Rising main, to manhole or STP")


def style_boundary(l):
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"style": "no", "outline_color": "#000000", "outline_width": "0.6"})))


def style_settlements(l):
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"style": "no", "outline_color": "#7f7f7f", "outline_width": "0.25", "outline_style": "dot"})))


def clone(proj, name):
    mgr = proj.layoutManager()
    old = mgr.layoutByName(name)
    if old:
        mgr.removeLayout(old)
    doc = QDomDocument()
    with open(TEMPLATE, encoding="utf-8") as fh:
        doc.setContent(fh.read())
    lay = QgsPrintLayout(proj); lay.initializeDefaults()
    lay.loadFromTemplate(doc, QgsReadWriteContext(), True)
    lay.setName(name); mgr.addLayout(lay)
    return lay


def fill_box(lay, rows, width=72.0):
    for it in list(lay.items()):
        if isinstance(it, QgsLayoutItemLabel) and not it.text().strip():
            lay.removeLayoutItem(it)
    for it in lay.items():
        if isinstance(it, QgsLayoutFrame) and isinstance(it.multiFrame(), QgsLayoutItemManualTable):
            mf = it.multiFrame()
            mf.setTableContents([[QgsTableCell(str(k)), QgsTableCell(str(v))] for k, v in rows])
            mf.setIncludeTableHeader(False)
            mf.setColumnWidths([width * 0.52, width * 0.48 - 3.0]); mf.refresh()
            h = ROW_MM * len(rows)
            it.attemptResize(QgsLayoutSize(width, h, UNIT_MM)); mf.recalculateFrameSizes()
            it.attemptMove(QgsLayoutPoint(BOX_ANCHOR[0] - width, BOX_ANCHOR[1] - h, UNIT_MM))
            it.setBackgroundEnabled(False); it.setFrameEnabled(False); mf.setBackgroundColor(QColor(255, 255, 255, 235))
            return


def clear_of_legend(mapitem, legend, ext):
    """The extent that draws `ext` entirely to the right of the legend, at the map item's own aspect ratio."""
    mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
    lp, ls = legend.positionWithUnits(), legend.sizeWithUnits()
    band = (lp.x() + ls.width() + 4.0 - mp.x()) / ms.width()
    aspect = ms.width() / ms.height()
    w = ext.width() / (1.0 - band); h = w / aspect
    if h < ext.height():
        h = ext.height(); w = h * aspect
    xmax = ext.xMaximum()
    yc = ext.center().y()
    return QgsRectangle(xmax - w, yc - h / 2, xmax, yc + h / 2)


def make_map(proj, name, title, stack, legend_layers, ext, rows, out_png):
    lay = clone(proj, name)
    mapitem = None
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap):
            it.setLayers(stack); it.setKeepLayerSet(True); it.zoomToExtent(ext); mapitem = it
        elif isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"):
                it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
            elif t and not t.startswith("N"):
                it.setText(title); it.attemptResize(QgsLayoutSize(230, 6.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))
    for it in lay.items():
        if isinstance(it, QgsLayoutItemLegend):
            it.setLinkedMap(mapitem); it.setAutoUpdateModel(False)
            it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 248))
            grp = it.model().rootGroup()
            for ch in list(grp.children()):
                grp.removeChildNode(ch)
            for l in legend_layers:
                node = grp.addLayer(l)
                r = l.renderer()
                if r is not None and r.type() in ("categorizedSymbol", "RuleRenderer"):
                    node.setCustomProperty("legend/title-style", "hidden")
            it.setTitle(""); it.setResizeToContents(True); it.adjustBoxSize()
            # a legend only takes its real size while it is drawn: a throwaway render at low resolution settles it
            tmp = QgsLayoutExporter(lay); ts = QgsLayoutExporter.ImageExportSettings(); ts.dpi = 25
            tmp.exportToImage(os.path.join(os.environ.get("TEMP", "."), "w17_legend_probe.png"), ts)
            # the legend sits over the map's left side: push the drawing right so it never hides a pipe or a label
            print(f"      legend {it.sizeWithUnits().width():.1f} x {it.sizeWithUnits().height():.1f} mm")
            mapitem.zoomToExtent(clear_of_legend(mapitem, it, ext))
    fill_box(lay, rows)
    credit = QgsLayoutItemLabel(lay); credit.setText("Satellite image: Esri World Imagery")
    tf = QgsTextFormat(); tf.setFont(QFont("Arial")); tf.setSize(5.0); tf.setColor(QColor("#4a4a4a")); credit.setTextFormat(tf)
    lay.addLayoutItem(credit); credit.attemptMove(QgsLayoutPoint(9.5, 199.5, UNIT_MM)); credit.attemptResize(QgsLayoutSize(60, 3.5, UNIT_MM))
    exp = QgsLayoutExporter(lay); s = QgsLayoutExporter.ImageExportSettings(); s.dpi = 200
    res = exp.exportToImage(out_png, s)
    print("   ", os.path.basename(out_png), "ok" if res == QgsLayoutExporter.Success else f"FAILED {res}")
    if res == QgsLayoutExporter.Success:      # the report takes its copy from its own img/ folder
        shutil.copy2(out_png, os.path.join(IMG, os.path.basename(out_png)))


def build(names):
    app = QgsApplication([], True); app.initQgis()      # GUI mode (offscreen): the layout exporter needs it for text
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    proj.setTitle("Ibri Sewer, TE Networks and STP: network options S1 to S7 (W17)")
    proj.writeEntry("Paths", "/Absolute", False)
    root = proj.layerTreeRoot()
    os.makedirs(MAPS, exist_ok=True); os.makedirs(IMG, exist_ok=True)

    def add(group, l, visible=True):
        if l is None:
            return None
        proj.addMapLayer(l, False); n = group.addLayer(l); n.setItemVisibilityChecked(visible); n.setExpanded(False); return l

    base = root.addGroup("Base")
    bnd = vec(os.path.join(F, "01_Boundaries", "Project_boundary_updated.shp"), "Project boundary")
    style_boundary(bnd); add(base, bnd)
    stl = vec(os.path.join(F, "02_Settlements", "Settlements.shp"), "Settlement boundary")
    style_settlements(stl); add(base, stl)
    roads = vec(os.path.join(F, "05_Roads", "Road_Centercline.shp"), "Road centrelines")
    if roads:
        roads.loadNamedStyle(os.path.join(ST, "Road_Centercline.qml")); add(base, roads, visible=False)
    # the exported maps use the local Esri mosaic (5 m): web tiles crash a standalone layout export; the project keeps
    # the Google layer, switched off, for work on screen
    gs = QgsRasterLayer(GOOGLE, "Satellite image (Google), for work on screen", "wms")
    gs.setOpacity(0.5)
    sat = QgsRasterLayer(os.path.join(F, "03_Imagery", "esri_satellite_5m_utm40n_masked.tif"), "Satellite image (Esri World Imagery)")
    sat.setOpacity(0.5)
    proj.addMapLayer(sat, False)          # a map item only draws layers the project owns
    sizes = size_legend_layer(); proj.addMapLayer(sizes, False)

    ext = QgsRectangle(bnd.extent()); ext.scale(1.06)
    for name in names:
        gpkg = os.path.join(F, "11_Network_options", f"{name}.gpkg")
        summ_p = os.path.join(W17, "results", name, f"{name}_summary.json")
        if not os.path.exists(gpkg) or not os.path.exists(summ_p):
            print(name, "skipped: no layers or summary yet"); continue
        S = json.load(open(summ_p, encoding="utf-8"))
        print(name, S["text"])
        g = root.addGroup(f"{name}: {S['text']}"); g.setExpanded(False); g.setItemVisibilityChecked(name == names[0])
        pz = vec(gpkg, "Pipes by plant zone", "pipes"); style_pipes_zone(pz, S["stp"]); add(g, pz)
        pd_ = vec(gpkg, "Pipes by depth", "pipes"); style_pipes_depth(pd_); add(g, pd_, visible=False)
        mh = vec(gpkg, "Deep manholes", "manholes"); style_manholes_deep(mh); add(g, mh, visible=False)
        rm = vec(gpkg, "Rising mains", "rising_mains"); style_rising(rm) if rm else None; add(g, rm)
        ps = vec(gpkg, "Pumping stations", "pumping_stations"); style_pumps(ps) if ps else None; add(g, ps)
        pl = vec(gpkg, "Treatment plants", "plants"); style_plants(pl) if pl else None; add(g, pl)

        # ---- data boxes, from the same summary the report reads
        plants = S["plants"]
        rows_net = [("STP" + ("s" if len(plants) > 1 else ""), ", ".join(f"{z} ({OLD[z]})" for z in plants))]
        for z, v in plants.items():
            rows_net.append((f"{z}: average 2030 / 2070", f"{fmt(v['avg_m3d']['2030'])} / {fmt(v['avg_m3d']['2070'])} m³/d"))
        rows_net += [("Sewers", f"{fmt(S['pipe_km'], 0)} km"),
                     ("Pumping stations", f"{S['pumping_stations']}, {fmt(S['kw'])} kW"),
                     ("Rising mains", f"{fmt(S['rising_main_m'] / 1000, 1)} km"),
                     ("Pumping energy 2030 / 2070", f"{fmt(S['mwh_2030'] / 1000, 2)} / {fmt(S['mwh_2070'] / 1000, 2)} GWh/yr")]
        rows_dep = [("Manholes", fmt(S["manholes"])), ("Deeper than 12 m", fmt(S["manholes_over_12"])),
                    ("Deepest", f"{S['deepest']['label']}, {S['deepest']['depth']:.1f} m"),
                    ("Sewer deeper than 12 m", f"{fmt(S['pipe_km_deeper_12'], 1)} km"),
                    ("Velocity above 3.0 m/s", f"{S['checks_2070']['v_over_3']} pipes"),
                    ("Depth of flow above G203 limit", f"{S['checks_2070']['dd_over']} pipes")]
        stack_net = [x for x in (pl, ps, rm, pz, stl, bnd, sat) if x is not None]
        leg_net = [x for x in (pl, ps, rm, pz, sizes, bnd) if x is not None]
        make_map(proj, f"W17 {name} network", f"Option {name}: {S['text']}, sewers and STP zones", stack_net, leg_net, ext,
                 rows_net, os.path.join(MAPS, f"W17_{name}_network.png"))
        stack_dep = [x for x in (pl, ps, mh, pd_, stl, bnd, sat) if x is not None]
        leg_dep = [x for x in (pl, ps, mh, pd_, sizes, bnd) if x is not None]
        make_map(proj, f"W17 {name} depth", f"Option {name}: depth of the 2070 design", stack_dep, leg_dep, ext,
                 rows_dep, os.path.join(MAPS, f"W17_{name}_depth.png"))
    root.addLayer(sat)
    proj.addMapLayer(gs, False); n = root.addLayer(gs); n.setItemVisibilityChecked(False)
    proj.write(PROJECT)
    print("wrote", PROJECT, "|", len(proj.mapLayers()), "layers |", len(proj.layoutManager().layouts()), "layouts")
    app.exitQgis()


if __name__ == "__main__":
    build(sys.argv[1:] or list(SCENARIOS))
