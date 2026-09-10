# Safe unload / reload of the W13 load layers inside QGIS.
#
# Why this file exists (2026-09-10): QGIS crashed twice while the layers were being swapped from a script.
#   05:45  QTabBar destructor during a layout resize  -> a layer was removed while its attribute table / selection panel was open
#   06:45  QgsMapCanvas::setLayersPrivate -> snapping utils -> freed expression context -> a layer was removed while the canvas
#          was still rendering it (77,000 plots with labels) and the snapping utilities still pointed at it
# The shapefiles have to be released before python rewrites them, so the layers must go; but they must go SAFELY:
# stop and freeze the canvas, close attribute tables, remove, let the event loop settle, then reload and unfreeze.
from qgis.core import (QgsProject, QgsVectorLayer, QgsFillSymbol, QgsMarkerSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsTextFormat, QgsTextBufferSettings, QgsApplication)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QCoreApplication
from qgis.utils import iface
import os, gc

W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W13"
KEYS = ('plots_load.shp', 'ele_meters_on_plots', 'settlements_merged')

def _settle():
    for _ in range(5): QCoreApplication.processEvents()

def unload_w13():
    proj = QgsProject.instance(); canvas = iface.mapCanvas()
    canvas.stopRendering(); canvas.freeze(True)
    # close attribute tables and any dialog that holds a layer
    for w in QgsApplication.topLevelWidgets():
        if w.__class__.__name__ in ('QgsAttributeTableDialog', 'QgsAttributeDialog'):
            try: w.close()
            except Exception: pass
    _settle()
    n = 0
    for l in list(proj.mapLayers().values()):
        src = os.path.normcase(l.source().split('|')[0])
        if any(k in src for k in KEYS):
            try: iface.setActiveLayer(None)
            except Exception: pass
            proj.removeMapLayer(l.id()); n += 1
    _settle(); gc.collect(); _settle()
    canvas.freeze(False)
    proj.write()
    return n

def reload_w13(render_map=False):
    proj = QgsProject.instance(); canvas = iface.mapCanvas(); canvas.freeze(True)
    root = proj.layerTreeRoot(); grp = root.findGroup('Claude W13 load') or root.insertGroup(0, 'Claude W13 load')
    def add(lyr):
        proj.addMapLayer(lyr, False); grp.addLayer(lyr); return lyr
    s = add(QgsVectorLayer(f"{W13}/shp/Settlements_merged.shp", "Settlements merged (W13)", "ogr"))
    s.renderer().setSymbol(QgsFillSymbol.createSimple({'style': 'no', 'outline_color': '#ffffff', 'outline_width': '0.7', 'outline_width_unit': 'MM'}))
    pal = QgsPalLayerSettings(); pal.fieldName = "SETTLE || '\\n' || \"POP_TODAY\" || ' -> ' || \"POP_ULT\" || '\\nfull ' || CASE WHEN \"SAT_YEAR\" > 0 THEN \"SAT_YEAR\" ELSE 'never' END"; pal.isExpression = True; pal.enabled = True
    tf = QgsTextFormat(); tf.setSize(9); tf.setColor(QColor('#ffffff')); b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(1); b.setColor(QColor('#000000')); tf.setBuffer(b); pal.setFormat(tf)
    s.setLabelsEnabled(True); s.setLabeling(QgsVectorLayerSimpleLabeling(pal))
    p = add(QgsVectorLayer(f"{W13}/shp/PLOTS_load.shp", "PLOTS load (W13)", "ogr"))
    cols = {'Residential': '#FFE600', 'Residential-Commercial': '#F5A742', 'Commercial': '#E03C31', 'Industrial': '#9B59B6', 'Government': '#3498DB',
            'Agricultural': '#4CAF50', 'Heritage': '#8d6e63', 'Unresolved': '#ff00ff', 'Unmetered': '#9E9E9E'}
    p.setRenderer(QgsCategorizedSymbolRenderer('DERIVED', [QgsRendererCategory(k, QgsFillSymbol.createSimple({'color': v if k != 'Unmetered' else '158,158,158,70', 'outline_color': '#333333', 'outline_width': '0.08', 'outline_width_unit': 'MM'}), k) for k, v in cols.items()]))
    m = add(QgsVectorLayer(f"{W13}/shp/ELE_meters_on_plots.shp", "Electricity meters on plots (W13)", "ogr"))
    mc = {'domestic': '#7fb3d5', 'non_domestic': '#e67e22', 'government': '#8e44ad', 'special': '#641e16', 'agricultural': '#52be80'}
    m.setRenderer(QgsCategorizedSymbolRenderer('GUD', [QgsRendererCategory(k, QgsMarkerSymbol.createSimple({'name': 'circle', 'color': v, 'outline_color': '#ffffff', 'outline_width': '0.15', 'size': '1.6'}), k) for k, v in mc.items()]))
    # the plot layer is heavy: leave it unchecked until the user wants it, so the canvas is not asked to draw 77,000 polygons on every pan
    root.findLayer(p.id()).setItemVisibilityChecked(False)
    _settle(); canvas.freeze(False); proj.write()
    counts = (p.featureCount(), m.featureCount(), s.featureCount())
    if render_map:
        src = open(f"{W13}/py/render_settlements_growth_map.py", encoding="utf-8").read()
        src = src.replace("'Government': '#3498DB', 'Agricultural': '#4CAF50'}.items():", "'Government': '#3498DB', 'Agricultural': '#4CAF50', 'Heritage': '#8d6e63'}.items():")
        g = {}; exec(src, g)
        for k in ('pl', 'sl', 'bl'): g.pop(k, None)
        gc.collect()
    return counts
