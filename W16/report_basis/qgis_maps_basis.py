"""Map figures for the Design Basis Report. Run inside QGIS (the qgis MCP bridge
execs this file) with the project QGIS 2621 ibri sewer stp2.qgz open.

Every map is a clone of the project's A4 landscape layout "W2 M1 Study Area" (loaded
from the older project on 2026-09-14), so all figures share one frame; each clone is
kept in the project as "RPT <key>" (engineer, 2026-09-14: keep all the map layouts).
The satellite image is drawn at 50 % opacity on a copy of the project's layer, so the
project's own layer is untouched. The free-meter panels are rendered one by one and
composed into pages by compose_panels.py; an atlas layout over the same panels is kept
in the project for browsing.
"""
import json
import os
import sys

from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer, QgsFillSymbol, QgsMarkerSymbol,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGraduatedSymbolRenderer,
                       QgsRendererRange, QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat,
                       QgsTextBufferSettings, QgsLayoutExporter, QgsLayoutItemLabel, QgsLayoutItemMap,
                       QgsLayoutItemLegend, QgsRectangle, QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes,
                       QgsMapSettings, QgsMapRendererParallelJob, QgsPrintLayout, QgsLayoutItemScaleBar,
                       QgsLayoutItemPage, QgsCoordinateReferenceSystem, QgsSingleSymbolRenderer)
from qgis.PyQt.QtCore import QSize
from qgis.PyQt.QtGui import QColor, QImage, QPainter

HERE = os.path.dirname(os.path.abspath(__file__))
W16 = os.path.dirname(HERE)
REPO = os.path.dirname(W16)
sys.path.insert(0, os.path.join(W16, "report"))
import qgis_maps as qm  # noqa: E402

# the plot-class overrides of facts_w14 (the treatment plant's plot, farm meters for its pumps,
# is a government site); copied here so the QGIS side needs no pandas
OVERRIDES = [("the Ibri treatment plant", (444342.5, 2562976.6), "Government")]   # = facts_w14.PLOT_OVERRIDES

IMG = os.path.join(HERE, "img")
PANELS = os.path.join(IMG, "panels")
SHP14 = os.path.join(REPO, "W14", "shp")
SHPB = os.path.join(HERE, "shp")
TOWNS = os.path.join(os.path.dirname(REPO), "SHP", "Towns", "Towns.shp")
SUBTITLE = "Ibri Sewer, TE Networks and STP — Design Basis Report | Renardet 2621"
BASEMAP_OPACITY = 0.5
UNIT_MM = QgsUnitTypes.LayoutMillimeters
NAVY = "#1F497D"

_L = {}


def _label(layer, expr, size=7.0, colour=NAVY, bold=False, buffer=0.8):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); tf.setSize(size); tf.setColor(QColor(colour))
    f = tf.font(); f.setBold(bold); tf.setFont(f)
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b)
    pal.setFormat(tf)
    layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))


def _label_two_years(layer, big_km2=25.0):
    """Every settlement labelled 'Name / 2055: q / 2070: q'; the large ones inside their polygon,
    the small ones outside it with a leader line, so the cluster west of Ibri does not overlap
    (engineer, 2026-09-14)."""
    from qgis.core import QgsRuleBasedLabeling, QgsSimpleLineCallout
    expr = """title("SETTLE") || '\\n' || '2055: ' || format_number("Q_2055", 0) || '\\n' || '2070: ' || format_number("Q_ULT", 0)"""

    def settings(outside):
        pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
        tf = QgsTextFormat(); tf.setSize(6.6); tf.setColor(QColor(NAVY))
        f = tf.font(); f.setBold(True); tf.setFont(f)
        b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(1.0); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b)
        pal.setFormat(tf)
        pal.multilineAlign = QgsPalLayerSettings.MultiCenter
        if outside:
            # around the centroid rather than along the edge: a tiny polygon has too few
            # edge candidates and two neighbours' labels end up on top of each other
            pal.placement = QgsPalLayerSettings.AroundPoint
            pal.centroidWhole = True
            pal.dist = 7.0
            co = QgsSimpleLineCallout(); co.setEnabled(True)
            co.lineSymbol().setColor(QColor(NAVY)); co.lineSymbol().setWidth(0.3)
            pal.setCallout(co)
        else:
            pal.placement = QgsPalLayerSettings.Horizontal
            pal.fitInPolygonOnly = True
        # every settlement gets a label, but the engine moves them apart first and only
        # overlaps when nothing else fits (displayAll would stack them at the first candidate)
        try:
            from qgis.core import Qgis
            ps = pal.placementSettings(); ps.setOverlapHandling(Qgis.LabelOverlapHandling.AllowOverlapIfRequired)
            pal.setPlacementSettings(ps)
        except Exception:
            pal.displayAll = True
        return pal

    root = QgsRuleBasedLabeling.Rule(QgsPalLayerSettings())
    big = QgsRuleBasedLabeling.Rule(settings(False)); big.setFilterExpression(f"$area >= {big_km2 * 1e6}"); big.setDescription("inside")
    small = QgsRuleBasedLabeling.Rule(settings(True)); small.setFilterExpression(f"$area < {big_km2 * 1e6}"); small.setDescription("outside, with a leader")
    root.appendChild(big); root.appendChild(small)
    layer.setLabelsEnabled(True); layer.setLabeling(QgsRuleBasedLabeling(root))


def layers():
    """The styled layers of the basis maps, added to the project but not to the tree."""
    if "_pn" in _L:
        return _L
    proj = QgsProject.instance()
    root = proj.layerTreeRoot()

    sm = QgsVectorLayer(os.path.join(SHP14, "Settlements_merged.shp"), "Settlement boundary, redrawn as a partition", "ogr")
    sm.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {'style': 'no', 'outline_color': NAVY, 'outline_width': '0.6', 'outline_width_unit': 'MM'})))
    _label(sm, 'title("SETTLE")', 7.0)

    r0 = QgsVectorLayer(TOWNS, "Settlement boundary as received (Inception Report)", "ogr")
    r0.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {'style': 'no', 'outline_color': '#C0504D', 'outline_width': '0.55', 'outline_width_unit': 'MM', 'outline_style': 'dash'})))

    po = QgsVectorLayer(os.path.join(SHP14, "PLOTS_load.shp"), "Cadastral plot", "ogr")
    po.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {'color': '255,242,122,70', 'outline_color': '#8a7a1a', 'outline_width': '0.05', 'outline_width_unit': 'MM'})))

    # the use of each plot: colour without an outline; only the empty plots keep a line
    pu = QgsVectorLayer(os.path.join(SHP14, "PLOTS_load.shp"), "Use of the plot", "ogr")
    cols = [('Residential', 'Residential', '#FFE600'), ('Residential-Commercial', 'Residential-Commercial', '#F5A742'),
            ('Commercial', 'Commercial', '#E03C31'), ('Government', 'Government', '#3498DB'),
            ('Agricultural', 'Agricultural', '#4CAF50'), ('Industrial', 'Industrial', '#9B59B6'),
            ('Heritage', 'Heritage, old quarter', '#8d6e63')]
    cats = [QgsRendererCategory(k, QgsFillSymbol.createSimple({'color': c, 'outline_style': 'no'}), lab) for k, lab, c in cols]
    cats.append(QgsRendererCategory('Unmetered', QgsFillSymbol.createSimple(
        {'style': 'no', 'outline_color': '#4a4a4a', 'outline_width': '0.11', 'outline_width_unit': 'MM'}), 'Empty plot, outline only'))
    # the class with the overrides applied in the expression, so the frozen layer is untouched
    expr = '"DERIVED"'
    for what, (x, y), cls in OVERRIDES:
        expr = f"CASE WHEN intersects($geometry, geom_from_wkt('POINT({x} {y})')) THEN '{cls}' ELSE {expr} END"
    pu.setRenderer(QgsCategorizedSymbolRenderer(expr, cats))

    # the settlements shaded by their saturation flow, each labelled with it
    qs = QgsVectorLayer(os.path.join(SHP14, "Settlements_merged.shp"), "Average sewage flow at saturation (2070), m³/d", "ogr")
    rngs = [(0, 100, 'under 100', '#eff3ff'), (100, 500, '100 to 500', '#c6dbef'), (500, 1000, '500 to 1,000', '#9ecae1'),
            (1000, 2500, '1,000 to 2,500', '#6baed6'), (2500, 5000, '2,500 to 5,000', '#3182bd'), (5000, 1e9, 'over 5,000', '#08519c')]
    qs.setRenderer(QgsGraduatedSymbolRenderer('Q_ULT', [
        QgsRendererRange(lo, hi, QgsFillSymbol.createSimple(
            {'color': '%d,%d,%d,150' % (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)), 'outline_color': NAVY,
             'outline_width': '0.45', 'outline_width_unit': 'MM'}), lab) for lo, hi, lab, c in rngs]))
    _label_two_years(qs)

    fm = QgsVectorLayer(os.path.join(SHPB, "free_meters.shp"), "Meter more than 15 m from any plot", "ogr")
    fm.setRenderer(QgsCategorizedSymbolRenderer('DWELLING', [
        QgsRendererCategory(1, QgsMarkerSymbol.createSimple(
            {'name': 'circle', 'color': '#C0504D', 'outline_color': '#ffffff', 'outline_width': '0.25', 'size': '2.4'}), 'Domestic meter'),
        QgsRendererCategory(0, QgsMarkerSymbol.createSimple(
            {'name': 'circle', 'color': '#4F81BD', 'outline_color': '#ffffff', 'outline_width': '0.25', 'size': '2.0'}), 'Other meter: shop, government, farm')]))

    pn = QgsVectorLayer(os.path.join(SHPB, "free_meter_panels.shp"), "Zoom panel (appendix)", "ogr")
    pn.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {'style': 'no', 'outline_color': '#333333', 'outline_width': '0.28', 'outline_width_unit': 'MM'})))
    _label(pn, '"PANEL"', 6.0, '#333333', bold=True, buffer=0.7)

    # the panel renders: the same points bigger, and the plots as clear outlines
    fmb = QgsVectorLayer(os.path.join(SHPB, "free_meters.shp"), "Meter (panel)", "ogr")
    fmb.setRenderer(QgsCategorizedSymbolRenderer('DWELLING', [
        QgsRendererCategory(1, QgsMarkerSymbol.createSimple(
            {'name': 'circle', 'color': '#C0504D', 'outline_color': '#ffffff', 'outline_width': '0.4', 'size': '3.6'}), 'Domestic meter'),
        QgsRendererCategory(0, QgsMarkerSymbol.createSimple(
            {'name': 'circle', 'color': '#4F81BD', 'outline_color': '#ffffff', 'outline_width': '0.4', 'size': '3.2'}), 'Other meter')]))
    pob = QgsVectorLayer(os.path.join(SHP14, "PLOTS_load.shp"), "Cadastral plot (panel)", "ogr")
    pob.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
        {'color': '255,242,122,55', 'outline_color': '#f2c100', 'outline_width': '0.35', 'outline_width_unit': 'MM'})))

    for l in (sm, r0, po, pu, qs, fm, pn, fmb, pob):
        # a copy left by an earlier run, outside the tree, is replaced
        for old in proj.mapLayersByName(l.name()):
            if root.findLayer(old.id()) is None:
                proj.removeMapLayer(old.id())
        proj.addMapLayer(l, False)
        _L[l.name()] = l
    _L["_fm"], _L["_pn"] = fm, pn
    return _L


def basemap():
    """A copy of the project's satellite layer at 50 % opacity."""
    if "_bm" in _L:
        return _L["_bm"]
    src = qm._basemap()
    if src is None:
        return None
    bm = QgsRasterLayer(src.source(), "Satellite image (Google)", src.providerType())
    bm.setOpacity(BASEMAP_OPACITY)
    QgsProject.instance().addMapLayer(bm, False)
    _L["_bm"] = bm
    return bm


def _overflow():
    r2 = qm._r2_layers()
    return r2["Capacity taken by overflow"], r2["Overflow, people"]


BOX_WIDTH = {"B03_saturation": 98.0, "B01_boundaries": 78.0, "B05_free_meters": 72.0}   # mm, where the text needs it

FIGURES = {
    # key: (title, layer names top to bottom, box key)
    "B01_boundaries": ("Settlement boundaries: as received, and redrawn as a partition",
                       ["Project Boundary updated", "Settlement boundary as received (Inception Report)",
                        "Settlement boundary, redrawn as a partition", "Cadastral plot"], "B01_boundaries"),
    "B02_landuse": ("Use of each plot, derived from the meters and the satellite",
                    ["Project Boundary updated", "Settlement boundary, redrawn as a partition", "Use of the plot"], "B02_landuse"),
    "B03_saturation": ("Average sewage flow of each settlement in 2055 and at saturation, 2070",
                       ["Project Boundary updated", "Average sewage flow at saturation (2070), m³/d"], "B03_saturation"),
    "B04_overflow": ("Where the growth goes once a settlement is full",
                     ["Project Boundary updated", "Capacity taken by overflow", "Overflow, people"], "M10_overflow"),
    "B05_free_meters": ("The meters more than 15 metres from any plot",
                        ["Project Boundary updated", "Meter more than 15 m from any plot",
                         "Settlement boundary, redrawn as a partition"], "B05_free_meters"),
}


def _boxes():
    b = json.load(open(os.path.join(IMG, "basis_boxes.json"), encoding="utf-8"))
    b.update(json.load(open(os.path.join(qm.OUT, "map_boxes.json"), encoding="utf-8")))
    return b


def _resolve(names):
    L = layers(); proj = QgsProject.instance(); out = []
    ov = dict(zip(("Capacity taken by overflow", "Overflow, people"), _overflow()))
    for n in names:
        if n in L:
            out.append(L[n])
        elif n in ov:
            out.append(ov[n])
        else:
            hit = [l for l in proj.mapLayers().values() if l.name() == n]
            if hit:
                out.append(hit[0])
            else:
                print("   missing layer:", n)
    return out


def build(keys=None, dpi=200):
    os.makedirs(IMG, exist_ok=True)
    proj = QgsProject.instance()
    utm = QgsCoordinateReferenceSystem("EPSG:32640")
    bnd = [l for l in proj.mapLayers().values() if l.name() == "Project Boundary updated"][0]
    ext = QgsRectangle(bnd.extent()); ext.scale(1.06)
    boxes = _boxes(); bm = basemap(); made = []
    for key, (title, names, boxkey) in FIGURES.items():
        if keys and key not in keys:
            continue
        print(key)
        lay = qm._clone("RPT " + key)
        stack = _resolve(names) + ([bm] if bm else [])
        legends = []
        for it in lay.items():
            if isinstance(it, QgsLayoutItemMap):
                it.setLayers(stack); it.setKeepLayerSet(True); it.zoomToExtent(ext)
            elif isinstance(it, QgsLayoutItemLegend):
                it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 248)); legends.append(it)
            elif isinstance(it, QgsLayoutItemLabel):
                t = it.text()
                if t.startswith("Ibri Sewer"):
                    it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
                elif t and not t.startswith("N"):
                    it.setText(title); it.attemptResize(QgsLayoutSize(220, 6.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))
        mapitem = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]
        for lg in legends:
            lg.setLinkedMap(mapitem); lg.setAutoUpdateModel(False)
            grp = lg.model().rootGroup()
            for ch in list(grp.children()):
                grp.removeChildNode(ch)
            for l in stack:
                if l is bm:
                    continue
                node = grp.addLayer(l)
                r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() in ("categorizedSymbol",):
                    node.setCustomProperty("legend/title-style", "hidden")
            lg.setTitle(""); lg.setResizeToContents(True); lg.adjustBoxSize()
        qm._fill_box(lay, [tuple(r) for r in boxes[boxkey]], width=BOX_WIDTH.get(key))
        path = os.path.join(IMG, key + ".png")
        settings = QgsLayoutExporter.ImageExportSettings(); settings.dpi = dpi
        res = QgsLayoutExporter(lay).exportToImage(path, settings)
        made.append((key, res == QgsLayoutExporter.Success, path))
        print("   ", "ok" if res == QgsLayoutExporter.Success else "FAILED")
    return made


def render_panels(width_px=1000, height_px=750):
    """One PNG per zoom panel: the meters, the plots as outlines, the satellite image."""
    os.makedirs(PANELS, exist_ok=True)
    L = layers(); bm = basemap()
    pn = L["_pn"]
    stack = [L["Meter (panel)"], L["Cadastral plot (panel)"]] + ([bm] if bm else [])
    n = 0
    for f in pn.getFeatures():
        ms = QgsMapSettings()
        ms.setLayers(stack)
        ms.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
        ms.setExtent(f.geometry().boundingBox())
        ms.setOutputSize(QSize(width_px, height_px))
        ms.setOutputDpi(150)
        ms.setBackgroundColor(QColor(255, 255, 255))
        job = QgsMapRendererParallelJob(ms); job.start(); job.waitForFinished()
        img = job.renderedImage()
        img.save(os.path.join(PANELS, "panel_%02d.png" % f["PANEL"]))
        n += 1
    print("panels rendered:", n)
    return n


def atlas_layout():
    """A small atlas layout over the panels, kept in the project for browsing."""
    proj = QgsProject.instance(); mgr = proj.layoutManager()
    name = "RPT B05 free-meter panels (atlas)"
    old = mgr.layoutByName(name)
    if old:
        mgr.removeLayout(old)
    L = layers(); bm = basemap()
    lay = QgsPrintLayout(proj); lay.initializeDefaults(); lay.setName(name)
    page = lay.pageCollection().page(0); page.setPageSize(QgsLayoutSize(120, 95, UNIT_MM))
    m = QgsLayoutItemMap(lay); m.attemptMove(QgsLayoutPoint(4, 11, UNIT_MM)); m.attemptResize(QgsLayoutSize(112, 80, UNIT_MM))
    m.setLayers([L["Meter (panel)"], L["Cadastral plot (panel)"]] + ([bm] if bm else [])); m.setKeepLayerSet(True)
    m.setFrameEnabled(True); m.setAtlasDriven(True); m.setAtlasScalingMode(QgsLayoutItemMap.Auto); m.setAtlasMargin(0.0)
    lay.addLayoutItem(m)
    lab = QgsLayoutItemLabel(lay); lab.setText("[% 'Panel ' || \"PANEL\" || '  —  ' || \"SETTLE\" || ', ' || \"N\" || ' meters' %]")
    lab.attemptMove(QgsLayoutPoint(4, 3, UNIT_MM)); lab.attemptResize(QgsLayoutSize(112, 7, UNIT_MM)); lay.addLayoutItem(lab)
    sb = QgsLayoutItemScaleBar(lay); sb.setLinkedMap(m); sb.setStyle("Single Box"); sb.setUnits(QgsUnitTypes.DistanceMeters)
    sb.setNumberOfSegments(2); sb.setNumberOfSegmentsLeft(0); sb.setUnitsPerSegment(100); sb.setUnitLabel("m")
    sb.attemptMove(QgsLayoutPoint(6, 84, UNIT_MM)); lay.addLayoutItem(sb)
    atlas = lay.atlas(); atlas.setCoverageLayer(L["_pn"]); atlas.setEnabled(True); atlas.setPageNameExpression('"PANEL"')
    atlas.setSortFeatures(True); atlas.setSortExpression('"PANEL"')
    mgr.addLayout(lay)
    return lay


def add_to_tree():
    """The two new layers, in a group of their own, so the engineer can find them."""
    proj = QgsProject.instance(); root = proj.layerTreeRoot(); L = layers()
    name = "Claude W16 basis"
    grp = root.findGroup(name)
    if grp is None:
        grp = root.insertGroup(0, name)
    for key in ("_pn", "_fm"):
        l = L[key]
        if root.findLayer(l.id()) is None:
            grp.addLayer(l)
    grp.setItemVisibilityChecked(False)


def run(dpi=200):
    made = build(dpi=dpi)
    n = render_panels()
    atlas_layout()
    add_to_tree()
    QgsProject.instance().write()
    print("figures:", [(k, ok) for k, ok, _ in made], "| panels", n, "| project saved")
    return made, n


if __name__ == "__console__":
    run()
