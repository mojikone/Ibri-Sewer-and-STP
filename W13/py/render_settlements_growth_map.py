# Map of the merged settlements with today's people, ultimate people and the fill year, over the plots by derived use (run inside QGIS).
from qgis.core import (QgsProject, QgsMapSettings, QgsMapRendererParallelJob, QgsRectangle, QgsCoordinateReferenceSystem, QgsVectorLayer,
                       QgsFillSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsRuleBasedRenderer)
from qgis.PyQt.QtCore import QSize, Qt, QRectF, QPointF
from qgis.PyQt.QtGui import QPainter, QColor, QFont, QPen, QBrush
import os
proj = QgsProject.instance(); W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W13"
crs = QgsCoordinateReferenceSystem('EPSG:32640')
sat = proj.mapLayer('_4647068c_9322_4bc8_ab29_bc25d5ed2edd')
bnd = proj.mapLayer('Project_Boundary_838d5f8c_ffae_418a_afaa_3dd92e9e4c42')
pl = QgsVectorLayer(f"{W13}/shp/PLOTS_load.shp", 'plots', 'ogr')
sl = QgsVectorLayer(f"{W13}/shp/Settlements_merged.shp", 'settle', 'ogr')
# plots: derived use for the built, and the empty ones that will take people in light green, the empty that take nothing in grey
root = QgsRuleBasedRenderer.Rule(None)
def rule(label, expr, color, outline='#333333'):
    r = QgsRuleBasedRenderer.Rule(QgsFillSymbol.createSimple({'color': color, 'outline_color': outline, 'outline_width': '0.05', 'outline_width_unit': 'MM'}), 0, 0, expr, label); root.appendChild(r)
for k, v in {'Residential': '#FFE600', 'Residential-Commercial': '#F5A742', 'Commercial': '#E03C31', 'Industrial': '#9B59B6', 'Government': '#3498DB', 'Agricultural': '#4CAF50'}.items():
    rule(k, f'"DERIVED" = \'{k}\'', v)
rule('empty, takes people', '"FUT_CAP" = 1', '#7CFC9A')
rule('empty, takes nothing', '"FUT_CAP" = 0 AND "DERIVED" = \'Unmetered\'', '120,120,120,90')
pl.setRenderer(QgsRuleBasedRenderer(root)); pl.setOpacity(0.85)
sl.renderer().setSymbol(QgsFillSymbol.createSimple({'style': 'no', 'outline_color': '#ffffff', 'outline_width': '1.0', 'outline_width_unit': 'MM'}))
bl = QgsVectorLayer(bnd.source(), 'bnd', 'ogr'); bl.renderer().setSymbol(QgsFillSymbol.createSimple({'style': 'no', 'outline_color': '#00e5ff', 'outline_width': '0.6', 'outline_width_unit': 'MM', 'outline_style': 'dash'}))
W, H = 3000, 1850; ext = QgsRectangle(430500, 2555500, 479000, 2583500)
ms = QgsMapSettings(); ms.setDestinationCrs(crs); ms.setOutputSize(QSize(W, H)); ms.setExtent(ext); ms.setBackgroundColor(QColor(20, 20, 20)); ms.setOutputDpi(120)
ms.setLayers([sl, bl, pl, sat]); job = QgsMapRendererParallelJob(ms); job.start(); job.waitForFinished(); img = job.renderedImage(); ext = ms.extent()
def px(E, N): return QPointF((E - ext.xMinimum()) / ext.width() * W, (ext.yMaximum() - N) / ext.height() * H)
p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
fS = QFont('Arial', 9); fB = QFont('Arial', 10, QFont.Bold); fT = QFont('Arial', 15, QFont.Bold)
placed = []
for f in sl.getFeatures():
    c = f.geometry().pointOnSurface().asPoint(); pt = px(c.x(), c.y())
    lab = f['SETTLE']; sat_y = int(f['SAT_YEAR']) if f['SAT_YEAR'] else 0
    note = f"{int(f['POP_TODAY']):,} today -> {int(f['POP_ULT']):,} at 2081 | full {sat_y if sat_y else 'never'} | {f['Q_ULT']:.0f} m3/d"
    p.setFont(fB); wl = p.fontMetrics().horizontalAdvance(lab); p.setFont(fS); wn = p.fontMetrics().horizontalAdvance(note)
    bw = max(wl, wn) + 14; bh = 38; bx, by = pt.x() - bw / 2, pt.y() - bh / 2
    bx = min(max(bx, 5), W - bw - 5); by = min(max(by, 45), H - bh - 5)
    for _ in range(14):
        r = QRectF(bx, by, bw, bh)
        if not any(r.intersects(q) for q in placed): break
        by += bh + 3
    r = QRectF(bx, by, bw, bh); placed.append(r)
    p.setPen(QPen(QColor('#ffffff'), 1)); p.setBrush(QBrush(QColor(0, 0, 0, 180))); p.drawRoundedRect(r, 4, 4)
    p.setPen(QColor('#ffffff')); p.setFont(fB); p.drawText(QPointF(bx + 7, by + 15), lab); p.setFont(fS); p.setPen(QColor('#e8e8e8')); p.drawText(QPointF(bx + 7, by + 30), note)
title = 'Settlements merged: people today and at ultimate (2081), the year each fills, sewage at ultimate. Plots: built by use, empty green = takes people'
p.setFont(fT); p.setPen(QColor('#ffffff')); p.setBrush(QBrush(QColor(0, 0, 0, 170))); tw = p.fontMetrics().horizontalAdvance(title) + 20
p.drawRect(QRectF(10, 10, tw, 32)); p.drawText(QPointF(20, 33), title)
items = [('project boundary', '#00e5ff'), ('settlement, merged', '#ffffff'), ('Residential', '#FFE600'), ('Residential-Commercial', '#F5A742'), ('Commercial', '#E03C31'),
         ('Industrial', '#9B59B6'), ('Government', '#3498DB'), ('Agricultural', '#4CAF50'), ('empty, takes people', '#7CFC9A'), ('empty, takes nothing', '#787878')]
lh = 18; lx, ly = 10, H - 10 - (len(items) * lh + 12)
p.setPen(QPen(QColor('#ffffff'), 1)); p.setBrush(QBrush(QColor(0, 0, 0, 175))); p.drawRect(QRectF(lx, ly, 230, len(items) * lh + 12)); p.setFont(fS)
for i, (txt, col) in enumerate(items):
    y = ly + 8 + i * lh; p.setPen(QPen(QColor(col), 1)); p.setBrush(QBrush(QColor(col))); p.drawRect(QRectF(lx + 8, y + 3, 14, 10)); p.setPen(QColor('#ffffff')); p.drawText(QPointF(lx + 28, y + 12), txt)
sb = 5000 / ext.width() * W; p.setPen(QPen(QColor('#ffffff'), 3)); p.drawLine(QPointF(W - 20 - sb, H - 24), QPointF(W - 20, H - 24)); p.setFont(fB); p.drawText(QPointF(W - 20 - sb, H - 30), '5 km')
p.end(); out = f"{W13}/img/W13_settlements_growth.png"; img.save(out); print('saved', out)
