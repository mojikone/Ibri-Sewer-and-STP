"""Map figures for the Concept Design Report.

Run this inside the QGIS Python console, or through the qgis MCP bridge. It
clones the project's existing A3 landscape layout for each figure so every map
carries the same frame, legend, scale bar and north arrow, then exports a PNG
into the report's img folder.
"""
import os

from qgis.core import (QgsLayoutExporter, QgsLayoutItemLabel, QgsLayoutItemMap,
                       QgsLayoutItemLegend, QgsProject, QgsRectangle,
                       QgsCoordinateTransform, QgsCoordinateReferenceSystem,
                       QgsLayoutItemPicture, QgsReadWriteContext)
from qgis.core import QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes
from qgis.core import QgsRasterLayer, QgsMapLayerLegendUtils
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import QDomDocument

UNIT_MM = QgsUnitTypes.LayoutMillimeters

OUT = (r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude"
       r"\W14\report\img")
TEMPLATE = "W2 M1 Study Area"
SUBTITLE = "Ibri Sewer, TE Networks and STP — Concept Design Report | Renardet 2621"

# figure key: (layout title, [layer names, drawn bottom to top], basemap,
#              [(label, value) rows for the data box])
FIGURES = {
    "M01_location": (
        "Project location and study area boundary",
        ["Project Boundary updated", "Towns"], True,
        [("Study area", "531.4 km2"), ("Settlements", "25"),
         ("Wilayat", "Ibri, Adh Dhahirah"), ("Projection", "UTM 40N, WGS 84")]),
    "M02_wastewater": (
        "Wastewater assets: constructed and proposed",
        ["Project Boundary updated", "Existing gravity sewer",
         "Existing treated effluent main", "Existing force mains",
         "Existing pumping station", "STP location"], True,
        [("Gravity sewer, built 2006", "111.6 km"),
         ("Gravity sewer, proposed", "199.3 km"),
         ("Force main, built 2006", "10.0 km"),
         ("Pumping main, proposed", "23.2 km"),
         ("Treated effluent, proposed", "45.7 km"),
         ("Pumping stations", "1"),
         ("Treatment plant", "1,800 m3/d")]),
    "M03_water": (
        "Potable water network within the study area",
        ["Project Boundary updated", "PAEW water mains",
         "PAEW water laterals", "PAEW facilities"], True,
        [("Water mains", "647.8 km"), ("Laterals", "8.1 km"),
         ("System valves", "1,586"), ("Hydrants", "568"),
         ("Source", "PAEW dataset")]),
    "M04_electricity": (
        "Electricity accounts by consumption category",
        ["Project Boundary updated", "Electricity accounts by category"], True,
        [("Accounts", "33,970"), ("Domestic", "22,588"),
         ("Non-domestic", "9,392"), ("Governmental", "967"),
         ("Agricultural", "523")]),
    "M05_settlements": (
        "Settlements and cadastral plots",
        ["Project Boundary updated", "Towns", "MoH_Plots"], True,
        [("Settlements", "25"), ("Population 2024", "116,456"),
         ("Occupancy rate", "5.32 persons"), ("Source", "NCSI, MoHUP")]),
    "M06_population": (
        "Where the population is concentrated",
        ["Project Boundary updated", "GHS POP 2025 IBRI"], True,
        [("Source", "GHS-POP 2025"), ("Grid cell", "100 m"),
         ("Densest cell", "237 persons"),
         ("Use", "where people are, not how many")]),
    # ---- Revision 2: the data boxes below are filled from img/map_boxes.json,
    # written by facts_w14.map_boxes(), so the map and the text agree
    "M04_electricity": (
        "Electricity meters by category, placed on the plots",
        ["Project Boundary updated", "Electricity meter"], True, "json"),
    "M05_settlements": (
        "Settlements and cadastral plots",
        ["Project Boundary updated", "Settlement boundary", "Cadastral plot"], True, "json"),
    "M07_landuse": (
        "Use of each plot, derived from the meters and the satellite",
        ["Project Boundary updated", "Settlement boundary", "Use of the plot"], True, "json"),
    "M08_special": (
        "Identified projects and special consumption",
        ["Project Boundary updated", "Settlement boundary", "Identified site",
         "Identified project"], True, "json"),
    "M09_saturation": (
        "Average sewage flow per plot at saturation",
        ["Project Boundary updated", "Settlement boundary", "Average sewage flow of the plot at saturation"], True, "json"),
    "M10_overflow": (
        "Where the growth goes once a settlement is full",
        ["Project Boundary updated", "Capacity taken by overflow", "Overflow, people"], True, "json"),
}

_R2 = {}


def _r2_layers():
    """Styled copies for the Revision 2 maps, added to the project but not to
    the layer tree, so the user's own layers keep their styling."""
    from qgis.core import (QgsVectorLayer, QgsFillSymbol, QgsMarkerSymbol,
                           QgsCategorizedSymbolRenderer, QgsRendererCategory,
                           QgsGraduatedSymbolRenderer, QgsRendererRange,
                           QgsPalLayerSettings, QgsVectorLayerSimpleLabeling,
                           QgsTextFormat, QgsTextBufferSettings, QgsFeature,
                           QgsGeometry, QgsPointXY, QgsField, QgsFields)
    from qgis.PyQt.QtCore import QVariant
    if _R2:
        return _R2
    proj = QgsProject.instance()
    W14 = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    shp = lambda n: os.path.join(W14, "shp", n)

    s = QgsVectorLayer(shp("Settlements_merged.shp"), "Settlement boundary", "ogr")
    s.setRenderer(type(s.renderer())(QgsFillSymbol.createSimple(
        {'style': 'no', 'outline_color': '#1F3B63', 'outline_width': '0.55', 'outline_width_unit': 'MM'})))
    pal = QgsPalLayerSettings(); pal.fieldName = 'title("SETTLE")'; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); tf.setSize(7); tf.setColor(QColor('#1F3B63'))
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(0.8); b.setColor(QColor('#FFFFFF')); tf.setBuffer(b)
    pal.setFormat(tf); s.setLabelsEnabled(True); s.setLabeling(QgsVectorLayerSimpleLabeling(pal))

    po = QgsVectorLayer(shp("PLOTS_load.shp"), "Cadastral plot", "ogr")
    po.setRenderer(type(po.renderer())(QgsFillSymbol.createSimple(
        {'color': '255,242,122,90', 'outline_color': '#8a7a1a', 'outline_width': '0.05', 'outline_width_unit': 'MM'})))

    # the meters, with the category names the report uses
    me = QgsVectorLayer(shp("ELE_meters_on_plots.shp"), "Electricity meter", "ogr")
    mc = [('domestic', 'Domestic', '#7fb3d5'), ('non_domestic', 'Non-domestic', '#e67e22'),
          ('government', 'Governmental', '#8e44ad'), ('special', 'Special: industrial', '#641e16'),
          ('agricultural', 'Agricultural, no sewage', '#52be80')]
    me.setRenderer(QgsCategorizedSymbolRenderer('GUD', [
        QgsRendererCategory(k, QgsMarkerSymbol.createSimple(
            {'name': 'circle', 'color': c, 'outline_color': '#ffffff', 'outline_width': '0.12', 'size': '1.3'}), lab)
        for k, lab, c in mc]))

    # the OSM footprints, named for the reader and without their own labels
    fp = QgsVectorLayer(shp("Identified_projects_OSM.shp"), "Identified site", "ogr")
    fc = [('landuse=industrial', 'Industrial area', '#9B59B6'), ('landuse=military', 'Army camp', '#6b8e23'),
          ('man_made=wastewater_plant', 'Treatment plant', '#1f77b4'), ('tourism=hotel', 'Hotel', '#e67e22')]
    fp.setRenderer(QgsCategorizedSymbolRenderer('kind', [
        QgsRendererCategory(k, QgsFillSymbol.createSimple(
            {'color': '%d,%d,%d,70' % (int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16)), 'outline_color': c,
             'outline_width': '0.6', 'outline_width_unit': 'MM'}), lab) for k, lab, c in fc]))

    pu = QgsVectorLayer(shp("PLOTS_load.shp"), "Use of the plot", "ogr")
    cols = [('Residential', 'Home', '#FFE600'), ('Residential-Commercial', 'Home and shop', '#F5A742'),
            ('Commercial', 'Shop', '#E03C31'), ('Government', 'Government', '#3498DB'),
            ('Agricultural', 'Farm', '#4CAF50'), ('Industrial', 'Industrial', '#9B59B6'),
            ('Heritage', 'Heritage, old quarter', '#8d6e63'), ('Unmetered', 'Empty plot', '158,158,158,60')]
    pu.setRenderer(QgsCategorizedSymbolRenderer('DERIVED', [
        QgsRendererCategory(k, QgsFillSymbol.createSimple(
            {'color': c, 'outline_color': '#333333', 'outline_width': '0.04', 'outline_width_unit': 'MM'}), lab)
        for k, lab, c in cols]))

    pf = QgsVectorLayer(shp("PLOTS_load.shp"), "Average sewage flow of the plot at saturation", "ogr")
    ranges = [(0.0001, 0.5, 'up to 0.5', '#deebf7'), (0.5, 1.0, '0.5 to 1', '#9ecae1'), (1.0, 2.0, '1 to 2', '#4292c6'),
              (2.0, 5.0, '2 to 5', '#2171b5'), (5.0, 1e9, 'over 5', '#08306b')]
    pf.setRenderer(QgsGraduatedSymbolRenderer('Q_ULT', [
        QgsRendererRange(lo, hi, QgsFillSymbol.createSimple(
            {'color': c, 'outline_style': 'no'}), f"{lab} m3/d") for lo, hi, lab, c in ranges]))

    # the special sites that have no footprint layer: points with a label
    fields = QgsFields(); fields.append(QgsField('name', QVariant.String))
    sp = QgsVectorLayer('Point?crs=EPSG:32640&field=name:string(60)', 'Identified project', 'memory')
    pr = sp.dataProvider(); feats = []
    for name, e, n in (("Al Tayyeb industrial area", 455400, 2572700), ("Tanam industrial area", 445300, 2561300),
                       ("Army camp", 442010, 2565140), ("Ibri View resort, planned", 451081, 2566161),
                       ("Existing treatment plant", 444387, 2563352)):
        f = QgsFeature(sp.fields()); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(e, n))); f.setAttributes([name]); feats.append(f)
    pr.addFeatures(feats); sp.updateExtents()
    sp.setRenderer(type(sp.renderer())(QgsMarkerSymbol.createSimple(
        {'name': 'circle', 'color': '#a61b1b', 'outline_color': '#ffffff', 'outline_width': '0.3', 'size': '2.6'})))
    pal2 = QgsPalLayerSettings(); pal2.fieldName = "name"; pal2.enabled = True
    tf2 = QgsTextFormat(); tf2.setSize(7.5); tf2.setColor(QColor('#a61b1b'))
    b2 = QgsTextBufferSettings(); b2.setEnabled(True); b2.setSize(0.9); b2.setColor(QColor('#FFFFFF')); tf2.setBuffer(b2)
    pal2.setFormat(tf2); pal2.placement = QgsPalLayerSettings.OrderedPositionsAroundPoint
    sp.setLabelsEnabled(True); sp.setLabeling(QgsVectorLayerSimpleLabeling(pal2))

    # the overflow map: receivers shaded by the share of their capacity that comes from outside, and one arrow per route
    import json
    from qgis.core import QgsLineSymbol, QgsArrowSymbolLayer, QgsGraduatedSymbolRenderer, QgsRendererRange
    rj = json.load(open(os.path.join(OUT, "routes.json"), encoding="utf-8"))
    sh = QgsVectorLayer(shp("Settlements_merged.shp"), "Capacity taken by overflow", "ogr")
    # INSHARE (inflow at saturation / capacity) is written on the layer by growth_by_settlement.py; the routes file carries the same value
    rngs = [(0.0, 0.05, 'under 5 %', None), (0.05, 0.25, '5 to 25 %', '254,224,210,150'), (0.25, 0.5, '25 to 50 %', '252,146,114,150'),
            (0.5, 0.8, '50 to 80 %', '239,59,44,150'), (0.8, 1.01, 'over 80 %', '165,15,21,160')]
    sh.setRenderer(QgsGraduatedSymbolRenderer('INSHARE', [
        QgsRendererRange(lo, hi, QgsFillSymbol.createSimple(
            {'color': c, 'outline_color': '#1F3B63', 'outline_width': '0.4', 'outline_width_unit': 'MM'} if c else
            {'style': 'no', 'outline_color': '#1F3B63', 'outline_width': '0.4', 'outline_width_unit': 'MM'}), lab)
        for lo, hi, lab, c in rngs]))
    pal3 = QgsPalLayerSettings(); pal3.fieldName = 'title("SETTLE")'; pal3.isExpression = True; pal3.enabled = True
    tf3 = QgsTextFormat(); tf3.setSize(7); tf3.setColor(QColor('#1F3B63')); b3 = QgsTextBufferSettings(); b3.setEnabled(True); b3.setSize(0.8); b3.setColor(QColor('#FFFFFF')); tf3.setBuffer(b3)
    pal3.setFormat(tf3); sh.setLabelsEnabled(True); sh.setLabeling(QgsVectorLayerSimpleLabeling(pal3))
    ar = QgsVectorLayer('LineString?crs=EPSG:32640&field=people:double&field=label:string(80)', "Overflow, people", 'memory')
    apr = ar.dataProvider(); feats = []
    for r in rj["routes"]:
        if r["people"] < 500:
            continue
        f = QgsFeature(ar.fields()); f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(r["x1"], r["y1"]), QgsPointXY(r["x2"], r["y2"])]))
        f.setAttributes([r["people"], f"{r['donor_name']} to {r['receiver_name']}"]); feats.append(f)
    apr.addFeatures(feats); ar.updateExtents()
    arngs = [(500, 2000, '500 to 2,000 people', 0.9), (2000, 5000, '2,000 to 5,000', 1.6), (5000, 10000, '5,000 to 10,000', 2.4), (10000, 1e9, 'over 10,000', 3.4)]
    def arrow(w):
        sym = QgsLineSymbol(); sym.deleteSymbolLayer(0)
        a = QgsArrowSymbolLayer(); a.setArrowWidth(w); a.setArrowStartWidth(w * 0.5); a.setHeadLength(4.5); a.setHeadThickness(3.2)
        a.setColor(QColor('#0b2a5b')); a.subSymbol().setColor(QColor('#0b2a5b'))
        sym.appendSymbolLayer(a); sym.setOpacity(0.85); return sym
    ar.setRenderer(QgsGraduatedSymbolRenderer('people', [QgsRendererRange(lo, hi, arrow(w), lab) for lo, hi, lab, w in arngs]))
    for l in (s, po, me, fp, pu, pf, sp, sh, ar):
        proj.addMapLayer(l, False)
        _R2[l.name()] = l
    return _R2


def _boxes_json():
    import json
    p = os.path.join(OUT, "map_boxes.json")
    with open(p, encoding="utf-8") as fh:
        return json.load(fh)


# a population grid is mostly empty, and the ramp paints zero a solid pale
# colour that would hide the satellite background across the whole sheet.
# The copy used for the figure renders zero transparent; the project layer
# and its style are left exactly as the user set them.
TRANSPARENT_ZERO = ("GHS POP 2025 IBRI",)
_copies = {}


def _zero_transparent(layer):
    from qgis.core import QgsRasterLayer, QgsRasterTransparency
    if layer.name() in _copies:
        return _copies[layer.name()]
    # a 100 m cell is one hectare, so the value is persons per hectare
    copy = QgsRasterLayer(layer.source(), "Population, persons per hectare",
                          layer.providerType())
    if not copy.isValid():
        return layer
    copy.setRenderer(layer.renderer().clone())

    # the ramp legend defaults to six decimal places and an unlabelled strip
    from qgis.core import QgsBasicNumericFormat, QgsColorRampLegendNodeSettings
    shader = copy.renderer().shader().rasterShaderFunction()
    st = QgsColorRampLegendNodeSettings()
    fmt = QgsBasicNumericFormat()
    fmt.setNumberDecimalPlaces(0)
    fmt.setShowTrailingZeros(False)
    st.setNumericFormat(fmt)
    st.setMinimumLabel("0   none")
    st.setMaximumLabel("130 and above")
    shader.setLegendSettings(st)
    shader.setLabelPrecision(0)

    tr = QgsRasterTransparency()
    px = QgsRasterTransparency.TransparentSingleValuePixel()
    px.min, px.max, px.percentTransparent = -0.0001, 0.0001, 100.0
    tr.setTransparentSingleValuePixelList([px])
    copy.renderer().setRasterTransparency(tr)
    QgsProject.instance().addMapLayer(copy, False)   # not in the layer tree
    _copies[layer.name()] = copy
    return copy


def _layers(names):
    proj = QgsProject.instance()
    found, missing = [], []
    for n in names:
        hit = [l for l in proj.mapLayers().values() if l.name() == n]
        if hit:
            found.append(_zero_transparent(hit[0])
                         if n in TRANSPARENT_ZERO else hit[0])
        else:
            missing.append(n)
    if missing:
        print("   missing layers:", missing)
    return found


def _basemap():
    proj = QgsProject.instance()
    for n in ("Google Satellite", "ESRI Satellite", "Google satellite hydbrid"):
        hit = [l for l in proj.mapLayers().values() if l.name() == n]
        if hit:
            return hit[0]
    return None


def _clone(name):
    """Copy the template layout so every figure shares one frame."""
    proj = QgsProject.instance()
    mgr = proj.layoutManager()
    old = mgr.layoutByName(name)
    if old:
        mgr.removeLayout(old)
    src = mgr.layoutByName(TEMPLATE)
    doc = QDomDocument()
    el = src.writeXml(doc, QgsReadWriteContext())
    doc.appendChild(el)
    new = type(src)(proj)
    new.loadFromTemplate(doc, QgsReadWriteContext(), True)
    new.setName(name)
    mgr.addLayout(new)
    return new


def build(keys=None, dpi=200):
    os.makedirs(OUT, exist_ok=True)
    proj = QgsProject.instance()
    utm = QgsCoordinateReferenceSystem("EPSG:32640")

    bnd = [l for l in proj.mapLayers().values()
           if l.name() == "Project Boundary updated"][0]
    ext = bnd.extent()
    if bnd.crs() != utm:
        ext = QgsCoordinateTransform(bnd.crs(), utm,
                                     proj.transformContext()).transform(ext)
    ext = QgsRectangle(ext)
    ext.scale(1.06)

    made = []
    _r2_layers()
    boxes = _boxes_json()
    for key, (title, names, basemap, box) in FIGURES.items():
        if keys and key not in keys:
            continue
        if box == "json":
            box = [tuple(r) for r in boxes[key]]
        print(key)
        lay = _clone("RPT " + key)
        legends = []

        stack = _layers(names)
        if basemap:
            bm = _basemap()
            if bm:
                stack = stack + [bm]

        for it in lay.items():
            if isinstance(it, QgsLayoutItemMap):
                it.setLayers(stack)
                it.setKeepLayerSet(True)
                it.zoomToExtent(ext)
            elif isinstance(it, QgsLayoutItemLegend):
                it.setBackgroundEnabled(True)
                it.setBackgroundColor(QColor(255, 255, 255, 248))   # opaque: a label must not show through
                legends.append(it)
            elif isinstance(it, QgsLayoutItemLabel):
                t = it.text()
                if t.startswith("Ibri Sewer"):
                    it.setText(SUBTITLE)
                    it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM))
                    it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
                elif t and not t.startswith("N"):
                    # the number belongs to the report caption alone; a map
                    # that numbers itself drifts as soon as a figure is added
                    it.setText(title)
                    it.attemptResize(QgsLayoutSize(200, 6.5, UNIT_MM))
                    it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))

        # the legend must list only what the map draws, not the whole project
        mapitem = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]
        for lg in legends:
            lg.setLinkedMap(mapitem)
            lg.setAutoUpdateModel(False)
            grp = lg.model().rootGroup()
            for ch in list(grp.children()):
                grp.removeChildNode(ch)
            for l in stack:
                if l.name() in ("Google Satellite", "ESRI Satellite",
                                "Google satellite hydbrid"):
                    continue
                node = grp.addLayer(l)
                # a categorised layer already names itself in each class
                # label, so the layer title above them would repeat it
                r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() == "categorizedSymbol":
                    node.setCustomProperty("legend/title-style", "hidden")
                # a raster legend leads with "Band 1 (Gray)", which says
                # nothing; keep the colour ramp and drop the band node
                if isinstance(l, QgsRasterLayer):
                    lg.model().refreshLayerLegend(node)
                    kids = lg.model().layerLegendNodes(node)
                    keep = [i for i, n in enumerate(kids)
                            if type(n).__name__ != "QgsSimpleLegendNode"]
                    if keep and len(keep) < len(kids):
                        QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep)
                        lg.model().refreshLayerLegend(node)
            lg.setTitle("")
            lg.setResizeToContents(True)
            lg.adjustBoxSize()

        _fill_box(lay, box)

        path = os.path.join(OUT, key + ".png")
        exp = QgsLayoutExporter(lay)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = dpi
        res = exp.exportToImage(path, settings)
        made.append((key, res == QgsLayoutExporter.Success, path))
        print("   ", "ok" if res == QgsLayoutExporter.Success else "FAILED")

    proj.write()
    return made


if __name__ == "__console__":
    build()


# the template carries an empty white label behind the data table; the table
# is hinged to that label's lower-right corner and the label itself removed
BOX_ANCHOR = (286.3, 201.9)     # mm from the top-left of the page
BOX_WIDTH = 58.0                # mm
ROW_MM = 5.60                   # generous: the frame must not clip a row


def _fill_box(lay, rows):
    """Write the figure's data table and hinge it to the lower-right corner."""
    from qgis.core import (QgsLayoutFrame, QgsLayoutItemManualTable,
                           QgsLayoutItemLabel, QgsTableCell, QgsLayoutSize,
                           QgsLayoutPoint)

    # drop the empty backing label
    for it in list(lay.items()):
        if isinstance(it, QgsLayoutItemLabel) and not it.text().strip():
            lay.removeLayoutItem(it)

    for it in lay.items():
        if not isinstance(it, QgsLayoutFrame):
            continue
        mf = it.multiFrame()
        if not isinstance(mf, QgsLayoutItemManualTable):
            continue
        mf.setTableContents(
            [[QgsTableCell(str(k)), QgsTableCell(str(v))] for k, v in rows])
        mf.setIncludeTableHeader(False)
        mf.refresh()

        # height follows the row count: querying the multiframe for its own
        # size reports the frame rather than the table, which leaves a blank
        # strip under the last row
        w = BOX_WIDTH
        h = ROW_MM * len(rows)
        it.attemptResize(QgsLayoutSize(w, h, UNIT_MM))
        mf.recalculateFrameSizes()
        it.attemptMove(QgsLayoutPoint(BOX_ANCHOR[0] - w,
                                      BOX_ANCHOR[1] - h, UNIT_MM))
        # the frame is sized generously so no row is clipped; its background
        # is therefore switched off and the table paints its own, otherwise a
        # blank strip shows beneath the last row
        it.setBackgroundEnabled(False)
        it.setFrameEnabled(False)
        mf.setBackgroundColor(QColor(255, 255, 255, 235))
        return True
    return False
