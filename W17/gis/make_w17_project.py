"""Build the W17 QGIS project (network options S1-S7) from W17/Options 2026-10, with its print layouts cloned from
the report's map frame, and export the maps. Runs in the standalone QGIS python, so it never touches a QGIS window:

    & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" make_w17_project.py [S1 S2 ...]

Maps, on the frame every R3 map uses (template_report_A3.qpt, extracted from stp2.qgz), current names only:
  overview (once): the 24 subnetworks as simple lines, one colour each, the outfalls labelled, the settlement boundaries.
  zones:   pipes as simple lines coloured by the STP they drain to, outfalls labelled, STPs with the inlet depth.
  network: pipes by STP with width by size; pumping stations as circles labelled "O21 8.3m 1,000 m3/d / PMP 15m
           126L/s" (outfall, its depth, the 2070 average flow through the station; pump head and duty); rising mains
           dashed with the arrow at mid-length; STPs labelled with the inlet depth and the 2070 average.
  depth:   pipes by depth to invert only (one width, light to dark red); pumping stations labelled with the outfall
           depth; along every run of pipes deeper than 12 m, the deepest manhole and its depth.
(Engineer's map notes, 2026-10-01.) The legend sits in the bottom-left corner, translucent, with short wrapped labels,
and the drawing is widened until neither the legend nor the data box covers a pipe. The background is Google
satellite at 50 %: the standalone layout exporter crashes on web tiles, so each map's background is first rendered
from the Google layer for that map's exact extent and size, and the saved project keeps the live Google layer.
The data box of each map is filled from results/S#/S#_summary.json, the same file the report reads.
"""
import json, os, shutil, sys, tempfile, time
sys.stdout.reconfigure(line_buffering=True)
# Qt's own Windows platform, not "offscreen": offscreen cannot see the Windows fonts and draws every glyph as a box
from qgis.core import (Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsRectangle, QgsPrintLayout, QgsReadWriteContext, QgsLayoutItemMap, QgsLayoutItemLegend,
                       QgsLayoutItemLabel, QgsLayoutExporter, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes, QgsLayoutFrame,
                       QgsLayoutItemManualTable, QgsTableCell, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsLineSymbol, QgsMarkerSymbol, QgsFillSymbol, QgsProperty, QgsSymbolLayer,
                       QgsPalLayerSettings, QgsTextFormat, QgsTextBufferSettings, QgsVectorLayerSimpleLabeling,
                       QgsSingleSymbolRenderer, QgsMarkerLineSymbolLayer, QgsGraduatedSymbolRenderer, QgsRendererRange,
                       QgsFeatureRequest, QgsMapSettings, QgsMapRendererSequentialJob, QgsFeature, QgsGeometry)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtXml import QDomDocument

HERE = os.path.dirname(os.path.abspath(__file__))
W17 = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(W17, "py"))
from routing import SCENARIOS, option_label

F = os.path.join(W17, "Options 2026-10")
ST = os.path.join(F, "_styles")
PROJECT = os.path.join(F, "Ibri_W17_network_options.qgz")
TEMPLATE = os.path.join(HERE, "template_report_A3.qpt")
MAPS = os.path.join(F, "Maps")
IMG = os.path.join(W17, "report", "img")
GOOGLE = ("crs=EPSG:3857&format&http-header:referer=&type=xyz&url=https://www.google.cn/maps/vt?lyrs%3Ds@189%26gl%3Dcn"
          "%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0")
SUBTITLE = "Ibri Sewer, TE Networks and STP — Concept Design Report | Renardet 2621"   # as on every R3 map: no revision
CREDIT = "Satellite image: Google"
CRS = QgsCoordinateReferenceSystem("EPSG:32640")
NAVY, PUMP = "#1F3B63", "#a61b1b"
UNIT_MM = QgsUnitTypes.LayoutMillimeters
DPI = 200
ZONE_COLOUR = {"O1": "#2E75B6", "O4": "#C0504D", "O9": "#70AD47", "O3": "#7030A0", "O16": "#ED7D31", "O22": "#00A6D6"}
# one colour per subnetwork O1...O24, all saturated enough to read on the 50 % satellite image
SUB_COLOUR = ["#e6194b", "#3cb44b", "#e0b400", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c",
              "#008080", "#6a3d9a", "#9a6324", "#800000", "#00c08b", "#808000", "#000075", "#ff4f8b", "#1f77b4",
              "#e08a00", "#2ca02c", "#8c564b", "#17becf", "#d62728", "#7f7f7f"]
DEPTH = [("up to 3 m", "#fcbba1"), ("3 to 6 m", "#fc9272"), ("6 to 9 m", "#fb6a4a"), ("9 to 12 m", "#de2d26"),
         ("12 to 15 m", "#a50f15"), ("over 15 m", "#67000d")]
WIDTH_EXPR = ('CASE WHEN "od_mm" >= 1400 THEN 2.0 WHEN "od_mm" >= 1000 THEN 1.6 WHEN "od_mm" >= 630 THEN 1.2 '
              'WHEN "od_mm" >= 400 THEN 0.85 WHEN "od_mm" >= 280 THEN 0.55 ELSE 0.28 END')
SIZE_CLASSES = [(0, 279, "200 to 250", 0.28), (280, 399, "280 to 355", 0.55), (400, 629, "400 to 560", 0.85),
                (630, 999, "630 to 900", 1.2), (1000, 1399, "1000 to 1200", 1.6), (1400, 9999, "1400 and over", 2.0)]
BOX_ANCHOR, ROW_MM = (286.3, 201.9), 5.6
LEGEND_ALPHA = 200          # the legend's white background, out of 255 (was 248): the map shows through


def fmt(n, d=0):
    return f"{n:,.{d}f}"


def text_format(size, colour=NAVY, bold=False, buffer=0.8):
    tf = QgsTextFormat(); f = QFont("Arial"); f.setBold(bold); tf.setFont(f); tf.setSize(size); tf.setColor(QColor(colour))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b)
    return tf


def label(layer, expr, size=5.5, colour=NAVY, bold=False, overlap=True, priority=8, dist=0.9):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    pal.setFormat(text_format(size, colour, bold)); pal.priority = priority
    if layer.geometryType() == Qgis.GeometryType.Point:
        pal.placement = Qgis.LabelPlacement.OrderedPositionsAroundPoint; pal.dist = dist
    pal.multilineAlign = Qgis.LabelMultiLineAlignment.Left
    if overlap:
        ps = pal.placementSettings(); ps.setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired); pal.setPlacementSettings(ps)
    layer.setLabeling(QgsVectorLayerSimpleLabeling(pal)); layer.setLabelsEnabled(True)


def line_symbol(colour, width=0.3, dd_width=False):
    s = QgsLineSymbol.createSimple({"color": colour, "width": str(width), "capstyle": "round", "joinstyle": "round"})
    if dd_width:
        s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression(WIDTH_EXPR))
    return s


def circle(colour, size, outline="#ffffff", width=0.3):
    return QgsMarkerSymbol.createSimple({"name": "circle", "color": colour, "outline_color": outline,
                                         "outline_width": str(width), "size": str(size)})


def vec(path, name, layer=None):
    l = QgsVectorLayer(path + (f"|layername={layer}" if layer else ""), name, "ogr")
    if not l.isValid():
        print("   INVALID:", path, layer); return None
    return l


def memory_line(name, colour, width=0.35):
    """A legend-only line entry (not drawn on the map)."""
    l = QgsVectorLayer("LineString?crs=EPSG:32640", name, "memory")
    l.setRenderer(QgsSingleSymbolRenderer(line_symbol(colour, width))); return l


# ------------------------------------------------------------------ styles
def style_pipes_zone(l, zones, sized):
    cats = [QgsRendererCategory(z, line_symbol(ZONE_COLOUR.get(z, "#555555"), 0.3 if not sized else 0.3, dd_width=sized),
                                f"To STP {z}") for z in zones]
    l.setRenderer(QgsCategorizedSymbolRenderer("zone", cats))


def style_pipes_sub(l):
    subs = [f"O{i}" for i in range(1, 25)]
    cats = [QgsRendererCategory(s, line_symbol(SUB_COLOUR[i], 0.35), s) for i, s in enumerate(subs)]
    l.setRenderer(QgsCategorizedSymbolRenderer("sub", cats))


def style_pipes_depth(l):
    cats = [QgsRendererCategory(b, line_symbol(c, 0.45), b) for b, c in DEPTH]
    l.setRenderer(QgsCategorizedSymbolRenderer("depth_band", cats))
    l.setName("Depth to invert")


def size_legend_layer():
    """Not drawn: a legend entry that explains the line widths (data-defined widths do not show in a legend)."""
    l = QgsVectorLayer("LineString?crs=EPSG:32640&field=od_mm:integer", "Pipe size, OD mm", "memory")
    rng = [QgsRendererRange(lo, hi, line_symbol("#555555", w), lab) for lo, hi, lab, w in SIZE_CLASSES]
    l.setRenderer(QgsGraduatedSymbolRenderer("od_mm", rng))
    return l


def style_pumps(l, field):
    l.setRenderer(QgsSingleSymbolRenderer(circle(PUMP, 2.4)))
    label(l, f'"{field}"', size=5.4, colour="#5a0f0f", priority=10)
    l.setName("Pumping station")


def style_plants(l, field):
    l.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple(
        {"name": "square", "color": NAVY, "outline_color": "#ffffff", "outline_width": "0.5", "size": "4.4"})))
    label(l, f'"{field}"', size=6.6, colour=NAVY, bold=True, priority=10, dist=1.2)
    l.setName("STP")


def style_outfalls(l):
    l.setRenderer(QgsSingleSymbolRenderer(circle("#1a1a1a", 1.6, width=0.25)))
    label(l, '"label"', size=6.0, colour="#1a1a1a", bold=True, priority=9, dist=0.6)
    l.setName("Outfall")


def style_deep(l):
    l.setRenderer(QgsSingleSymbolRenderer(circle("#67000d", 2.2, width=0.35)))
    label(l, '"map_label"', size=5.6, colour="#67000d", bold=True, priority=10, dist=0.6)
    l.setName("Deepest manhole~of a run over 12 m")


def style_rising(l, width=0.55):
    sym = QgsLineSymbol.createSimple({"color": PUMP, "width": str(width), "line_style": "dash", "capstyle": "round"})
    head = QgsMarkerLineSymbolLayer(True); head.setPlacements(Qgis.MarkerLinePlacement.CentralPoint)
    mk = QgsMarkerSymbol.createSimple({"name": "filled_arrowhead", "color": PUMP, "outline_style": "no", "size": "3.2"})
    head.setSubSymbol(mk); sym.appendSymbolLayer(head)
    l.setRenderer(QgsSingleSymbolRenderer(sym))
    l.setName("Rising main")


def style_boundary(l):
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"style": "no", "outline_color": "#000000", "outline_width": "0.5"})))
    l.setName("Project boundary")


def style_settlements(l, solid=False):
    l.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {"style": "no", "outline_color": "#3a3a3a" if solid else "#7f7f7f", "outline_width": "0.2" if solid else "0.25",
         "outline_style": "solid" if solid else "dot"})))
    l.setName("Settlement boundary")


# ------------------------------------------------------------------ layout
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
            return it


def clear_extent(mapitem, boxes, ext, test_layers):
    """The extent, at the map item's aspect ratio, that shows `ext` with no feature of `test_layers` under any of the
    layout boxes (legend bottom-left, data box bottom-right). It grows away from the top, and to the left or right of
    whichever box is hit, so the drawing moves into the free part of the frame and nothing is cut off."""
    ms, mp = mapitem.sizeWithUnits(), mapitem.positionWithUnits()
    aspect = ms.width() / ms.height()
    w, h = ext.width(), ext.height()
    if w / h < aspect:
        w = h * aspect
    else:
        h = w / aspect
    c = ext.center()
    # the drawing starts against the top of the frame, so the slack falls at the foot where the legend and box are
    E = QgsRectangle(c.x() - w / 2, ext.yMaximum() - h, c.x() + w / 2, ext.yMaximum())
    for _ in range(40):
        hit = set()
        for item, side in boxes:
            p, s = item.positionWithUnits(), item.sizeWithUnits()
            x0 = E.xMinimum() + (p.x() - mp.x()) / ms.width() * E.width()
            x1 = E.xMinimum() + (p.x() + s.width() - mp.x()) / ms.width() * E.width()
            y1 = E.yMaximum() - (p.y() - mp.y()) / ms.height() * E.height()
            y0 = E.yMaximum() - (p.y() + s.height() - mp.y()) / ms.height() * E.height()
            req = QgsFeatureRequest().setFilterRect(QgsRectangle(x0, y0, x1, y1)).setFlags(QgsFeatureRequest.ExactIntersect).setLimit(1)
            if any(next(l.getFeatures(req), None) is not None for l in test_layers if l is not None):
                hit.add(side)
        if not hit:
            return E
        xmin, xmax = E.xMinimum(), E.xMaximum()
        if "left" in hit:
            xmin -= E.width() * 0.03
        if "right" in hit:
            xmax += E.width() * 0.03
        nh = (xmax - xmin) / aspect
        E = QgsRectangle(xmin, E.yMaximum() - nh, xmax, E.yMaximum())
    print("      could not clear the boxes in 40 steps")
    return E


def google_background(proj, google, mapitem, tag):
    """Render the Google layer for the map item's exact extent and size, as a georeferenced PNG the exporter can draw."""
    ext = mapitem.extent(); s = mapitem.sizeWithUnits()
    w, h = int(round(s.width() / 25.4 * DPI)), int(round(s.height() / 25.4 * DPI))
    ms = QgsMapSettings(); ms.setLayers([google]); ms.setDestinationCrs(CRS); ms.setExtent(ext)
    ms.setOutputSize(QSize(w, h)); ms.setBackgroundColor(QColor("white"))
    job = QgsMapRendererSequentialJob(ms); job.start()
    t0 = time.time()
    while job.isActive() and time.time() - t0 < 180:
        QgsApplication.processEvents(); time.sleep(0.02)
    vis = ms.visibleExtent()
    path = os.path.join(tempfile.gettempdir(), f"w17_bg_{tag}.png")
    job.renderedImage().save(path)
    px, py = vis.width() / w, vis.height() / h
    with open(path[:-4] + ".pgw", "w") as fh:
        fh.write(f"{px}\n0\n0\n{-py}\n{vis.xMinimum() + px / 2}\n{vis.yMaximum() - py / 2}\n")
    r = QgsRasterLayer(path, "Satellite image (Google)"); r.setCrs(CRS); r.setOpacity(0.5)
    proj.addMapLayer(r, False)
    return r


def make_map(proj, google, name, title, stack, legend_layers, ext, rows, out_png, test_layers):
    lay = clone(proj, name)
    mapitem = legend = None
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap):
            it.setLayers(stack + [google]); it.setKeepLayerSet(True); it.zoomToExtent(ext); mapitem = it
        elif isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"):
                it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
            elif t and not t.startswith("N"):
                it.setText(title); it.attemptResize(QgsLayoutSize(230, 6.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))
        elif isinstance(it, QgsLayoutItemLegend):
            legend = it
    box = fill_box(lay, rows)
    if legend is not None:
        legend.setLinkedMap(mapitem); legend.setAutoUpdateModel(False)
        legend.setBackgroundEnabled(True); legend.setBackgroundColor(QColor(255, 255, 255, LEGEND_ALPHA))
        legend.setWrapString("~")                       # short labels, broken where they would widen the legend
        grp = legend.model().rootGroup()
        for ch in list(grp.children()):
            grp.removeChildNode(ch)
        for l in legend_layers:
            node = grp.addLayer(l)
            r = l.renderer()
            if r is not None and r.type() in ("categorizedSymbol", "RuleRenderer") and not l.name().startswith(("Depth", "Pipe size")):
                node.setCustomProperty("legend/title-style", "hidden")
        legend.setTitle(""); legend.setResizeToContents(True); legend.adjustBoxSize()
        # a legend only takes its real size while it is drawn: a throwaway render at low resolution settles it
        tmp = QgsLayoutExporter(lay); ts = QgsLayoutExporter.ImageExportSettings(); ts.dpi = 25
        mapitem.setLayers(stack)                        # the probe needs no background
        tmp.exportToImage(os.path.join(tempfile.gettempdir(), "w17_legend_probe.png"), ts)
        sz = legend.sizeWithUnits(); mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
        legend.attemptMove(QgsLayoutPoint(mp.x() + 3.0, mp.y() + ms.height() - sz.height() - 3.0, UNIT_MM))   # bottom left
        print(f"      legend {sz.width():.1f} x {sz.height():.1f} mm")
    boxes = ([(legend, "left")] if legend is not None else []) + ([(box, "right")] if box is not None else [])
    mapitem.zoomToExtent(clear_extent(mapitem, boxes, ext, test_layers))
    bg = google_background(proj, google, mapitem, name.replace(" ", "_"))
    mapitem.setLayers(stack + [bg])
    credit = QgsLayoutItemLabel(lay); credit.setText(CREDIT)
    tf = QgsTextFormat(); tf.setFont(QFont("Arial")); tf.setSize(5.0); tf.setColor(QColor("#4a4a4a")); credit.setTextFormat(tf)
    lay.addLayoutItem(credit); credit.attemptResize(QgsLayoutSize(40, 3.5, UNIT_MM))
    mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
    cx = (legend.positionWithUnits().x() + legend.sizeWithUnits().width() + 2.0) if legend is not None else mp.x() + 1.5
    credit.attemptMove(QgsLayoutPoint(cx, mp.y() + ms.height() - 4.2, UNIT_MM))      # beside the legend, at the foot
    exp = QgsLayoutExporter(lay); s = QgsLayoutExporter.ImageExportSettings(); s.dpi = DPI
    res = exp.exportToImage(out_png, s)
    print("   ", os.path.basename(out_png), "ok" if res == QgsLayoutExporter.Success else f"FAILED {res}")
    if res == QgsLayoutExporter.Success:      # the report takes its copy from its own img/ folder
        shutil.copy2(out_png, os.path.join(IMG, os.path.basename(out_png)))
    mapitem.setLayers(stack + [google])       # the saved layout draws the live Google layer
    proj.removeMapLayer(bg.id())


def build(names):
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(CRS)
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
    stl2 = vec(os.path.join(F, "02_Settlements", "Settlements.shp"), "Settlement boundary")
    style_settlements(stl2, solid=True); proj.addMapLayer(stl2, False)       # the overview's thin solid version
    roads = vec(os.path.join(F, "05_Roads", "Road_Centercline.shp"), "Road centrelines")
    if roads:
        roads.loadNamedStyle(os.path.join(ST, "Road_Centercline.qml")); add(base, roads, visible=False)
    google = QgsRasterLayer(GOOGLE, "Satellite image (Google)", "wms"); google.setOpacity(0.5)
    proj.addMapLayer(google, False)
    sizes = size_legend_layer(); proj.addMapLayer(sizes, False)
    ext = QgsRectangle(bnd.extent()); ext.scale(1.04)
    # the boundary as a line, for the legend test only (a polygon would "hit" everywhere inside it)
    bline = QgsVectorLayer("LineString?crs=EPSG:32640", "boundary line", "memory"); feats = []
    for f in bnd.getFeatures():
        g = f.geometry()
        for part in (g.asMultiPolygon() if g.isMultipart() else [g.asPolygon()]):
            for ring in part:
                nf = QgsFeature(); nf.setGeometry(QgsGeometry.fromPolylineXY(ring)); feats.append(nf)
    bline.dataProvider().addFeatures(feats); bline.updateExtents()

    # ---- the overview: every subnetwork in its own colour, the outfalls, the settlements (once, from the first option)
    first = next((n for n in names if os.path.exists(os.path.join(F, "11_Network_options", f"{n}.gpkg"))), None)
    if first:
        gpkg = os.path.join(F, "11_Network_options", f"{first}.gpkg")
        g = root.addGroup("Subnetworks (overview)"); g.setExpanded(False)
        sp = vec(gpkg, "Sewers by subnetwork", "pipes"); style_pipes_sub(sp); add(g, sp)
        of = vec(gpkg, "Outfall", "outfalls"); style_outfalls(of); add(g, of)
        S = json.load(open(os.path.join(W17, "results", first, f"{first}_summary.json"), encoding="utf-8"))
        leg_sub = memory_line("Sewer,~one colour per subnetwork", "#4363d8"); proj.addMapLayer(leg_sub, False)
        print("overview")
        make_map(proj, google, "W17 subnetworks", "The sewer network: twenty-four subnetworks and their outfalls",
                 [of, sp, stl2, bnd], [leg_sub, of, stl2, bnd], ext,
                 [("Subnetworks", "24"), ("Sewer", f"{fmt(S['pipe_km'])} km"), ("Manholes", fmt(S["manholes"])),
                  ("Settlements", "25")],
                 os.path.join(MAPS, "W17_overview_subnetworks.png"), [sp, of, bline])

    for name in names:
        gpkg = os.path.join(F, "11_Network_options", f"{name}.gpkg")
        summ_p = os.path.join(W17, "results", name, f"{name}_summary.json")
        if not os.path.exists(gpkg) or not os.path.exists(summ_p):
            print(name, "skipped: no layers or summary yet"); continue
        S = json.load(open(summ_p, encoding="utf-8"))
        lab = option_label(name)
        print(name, lab)
        g = root.addGroup(f"{name}: {lab}"); g.setExpanded(False); g.setItemVisibilityChecked(name == names[0])
        pz = vec(gpkg, "Sewers by STP", "pipes"); style_pipes_zone(pz, S["stp"], sized=False); add(g, pz, visible=False)
        pzs = vec(gpkg, "Sewers by STP and size", "pipes"); style_pipes_zone(pzs, S["stp"], sized=True); add(g, pzs)
        pd_ = vec(gpkg, "Depth to invert", "pipes"); style_pipes_depth(pd_); add(g, pd_, visible=False)
        dr = vec(gpkg, "Deepest manhole~of a run over 12 m", "deep_runs")
        if dr:
            style_deep(dr); add(g, dr, visible=False)
        rm = vec(gpkg, "Rising main", "rising_mains"); style_rising(rm) if rm else None; add(g, rm)
        ps = vec(gpkg, "Pumping station", "pumping_stations"); style_pumps(ps, "map_label") if ps else None; add(g, ps)
        psd = vec(gpkg, "Pumping station", "pumping_stations"); style_pumps(psd, "depth_label") if psd else None
        proj.addMapLayer(psd, False)
        pl = vec(gpkg, "STP", "plants"); style_plants(pl, "map_label") if pl else None; add(g, pl)
        pls = vec(gpkg, "STP", "plants"); style_plants(pls, "short_label") if pls else None
        proj.addMapLayer(pls, False)
        of = vec(gpkg, "Outfall", "outfalls"); style_outfalls(of); add(g, of, visible=False)
        of.setSubsetString('"is_plant" = 0')            # a plant's outfall carries the STP label instead
        rm_thin = vec(gpkg, "Rising main", "rising_mains"); style_rising(rm_thin, 0.4) if rm_thin else None
        proj.addMapLayer(rm_thin, False)

        plants = S["plants"]
        # one row per STP: the 2070 average and the depth of the sewer arriving at it
        box_plants = [(f"STP {z}, 2070", f"{fmt(v['avg_m3d']['2070'])} m³/d, {v['inlet_depth_m']:.1f} m deep")
                      for z, v in plants.items()]
        # zones: simple lines by STP, outfalls labelled, STPs with the inlet depth
        make_map(proj, google, f"W17 {name} zones", f"Option {name}: {lab}",
                 [x for x in (pls, of, rm_thin, pz, stl, bnd) if x is not None],
                 [x for x in (pls, of, rm_thin, pz, bnd) if x is not None], ext,
                 box_plants, os.path.join(MAPS, f"W17_{name}_zones.png"), [pz, of, bline])
        # network: sizes, pumping stations, rising mains
        make_map(proj, google, f"W17 {name} network", f"Option {name}: sewers, pumping stations and rising mains",
                 [x for x in (pl, ps, rm, pzs, stl, bnd) if x is not None],
                 [x for x in (pl, ps, rm, pzs, sizes, bnd) if x is not None], ext,
                 box_plants + [("Sewers", f"{fmt(S['pipe_km'])} km"),
                               ("Pumping stations", f"{S['pumping_stations']}, {fmt(S['kw'])} kW"),
                               ("Rising mains", f"{fmt(S['rising_main_m'] / 1000, 1)} km"),
                               ("Pumping energy 2030 / 2070",
                                f"{fmt(S['mwh_2030'] / 1000, 2)} / {fmt(S['mwh_2070'] / 1000, 2)} GWh/yr")],
                 os.path.join(MAPS, f"W17_{name}_network.png"), [pzs, ps, pl, bline])
        # depth: one thing only, the depth to invert
        km = S["pipe_km_by_band"]
        rows_dep = [("Sewer up to 3 m deep", f"{fmt(km.get('0-1.5 m', 0) + km.get('1.5-3 m', 0), 1)} km"),
                    ("3 to 6 m", f"{fmt(km.get('3-4.5 m', 0) + km.get('4.5-6 m', 0), 1)} km"),
                    ("6 to 9 m", f"{fmt(km.get('6-9 m', 0), 1)} km"), ("9 to 12 m", f"{fmt(km.get('9-12 m', 0), 1)} km"),
                    ("Deeper than 12 m", f"{fmt(km.get('>12 m', 0), 1)} km"),
                    ("Deepest manhole", f"{S['deepest']['depth']:.1f} m")]
        make_map(proj, google, f"W17 {name} depth", f"Option {name}: depth of the sewers to invert",
                 [x for x in (pls, psd, dr, pd_, bnd) if x is not None],
                 [x for x in (pd_, dr, psd, pls, bnd) if x is not None], ext,
                 rows_dep, os.path.join(MAPS, f"W17_{name}_depth.png"), [pd_, psd, bline])
    root.addLayer(google)
    proj.write(PROJECT)
    print("wrote", PROJECT, "|", len(proj.mapLayers()), "layers |", len(proj.layoutManager().layouts()), "layouts")
    app.exitQgis()


if __name__ == "__main__":
    build(sys.argv[1:] or list(SCENARIOS))
