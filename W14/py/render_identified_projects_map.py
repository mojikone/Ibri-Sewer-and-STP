# Renders two PNG maps of the identified projects for the engineer (run inside QGIS).
from qgis.core import (QgsProject, QgsMapSettings, QgsMapRendererParallelJob, QgsRectangle, QgsPointXY,
                       QgsCoordinateReferenceSystem, QgsCoordinateTransform, QgsVectorLayer, QgsFillSymbol,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsGeometry)
from qgis.PyQt.QtCore import QSize, Qt, QRectF, QPointF
from qgis.PyQt.QtGui import QImage, QPainter, QColor, QFont, QPen, QBrush, QPolygonF
import math, os

proj = QgsProject.instance()
OUT = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14/img"
os.makedirs(OUT, exist_ok=True)
crs = QgsCoordinateReferenceSystem('EPSG:32640')
sat = proj.mapLayer('_4647068c_9322_4bc8_ab29_bc25d5ed2edd')      # Google satellite hybrid
bnd = proj.mapLayer('Project_Boundary_838d5f8c_ffae_418a_afaa_3dd92e9e4c42')
plots = proj.mapLayer('PLOTS_59e7ed1e_b22c_49e9_a772_f89c0f58fca6')
sites = [l for l in proj.mapLayers().values() if l.name() == 'Identified projects, OSM footprints (W13)'][0]
tb = proj.mapLayer('W14_test_boundary_8b516ac7_76da_4ddc_8225_03353c5a3c06')

# a filled copy of the plots for the map only (the project keeps its outline style)
pl = QgsVectorLayer(plots.source(), 'plots_fill', 'ogr')
pal = {'Residential': '#FFF27A', 'Residential-Commercial': '#F5A742', 'Commercial': '#E03C31', 'Industrial': '#9B59B6',
       'Agricultural': '#6DBF4B', 'Tourism': '#5DADE2', 'Proposed': '#BDBDBD'}
cats = [QgsRendererCategory(k, QgsFillSymbol.createSimple({'color': v, 'outline_style': 'no'}), k) for k, v in pal.items()]
pl.setRenderer(QgsCategorizedSymbolRenderer('Classes', cats)); pl.setOpacity(0.75)
bl = QgsVectorLayer(bnd.source(), 'bnd', 'ogr')
bl.setRenderer(bnd.renderer().clone()) if False else None
bl.renderer().setSymbol(QgsFillSymbol.createSimple({'style': 'no', 'outline_color': '#ffffff', 'outline_width': '1.2', 'outline_width_unit': 'MM'}))
tl = QgsVectorLayer(tb.source(), 'tb', 'ogr')
tl.renderer().setSymbol(QgsFillSymbol.createSimple({'style': 'no', 'outline_color': '#00e5ff', 'outline_width': '0.8', 'outline_width_unit': 'MM', 'outline_style': 'dash'}))
sl = QgsVectorLayer(sites.source(), 'sites', 'ogr')
scol = {'landuse=industrial': '#c724ff', 'landuse=military': '#a3ff3b', 'man_made=wastewater_plant': '#00b7ff', 'tourism=hotel': '#ff9d00'}
sl.setRenderer(QgsCategorizedSymbolRenderer('kind', [QgsRendererCategory(k, QgsFillSymbol.createSimple({'color': '%d,%d,%d,85' % (int(v[1:3],16), int(v[3:5],16), int(v[5:7],16)), 'outline_color': v, 'outline_width': '0.9', 'outline_width_unit': 'MM'}), k) for k, v in scol.items()]))

# points to annotate: (E, N, label, note, colour)
STP = (444387, 2563352)
PTS = [
    (455400, 2572700, 'Al Tayyeb industrial area', '94 ha, 202 industrial plots, 1,035 shop meters. Existing 2006 sewers', '#c724ff'),
    (445300, 2561300, 'Tanam industrial area', '61 ha, 105 industrial plots, 409 shop meters. On the new network', '#c724ff'),
    (442010, 2565140, 'Army camp (NFR, Malik bin Faham)', '296 ha, no meter. Outside the network, revisit at report update', '#a3ff3b'),
    (451081, 2566161, 'Ibri View resort site (As Sulayf)', '2 km2 planned: 3 hotels, mall, housing. Not in cadastre. Later years only', '#ff3b3b'),
    (441384, 2569109, 'Ibri Regional Hospital', '240 beds. Governmental', '#ffffff'),
    (STP[0], STP[1], 'Existing STP', 'inlet 323.0 m', '#00b7ff'),
    (434150, 2555031, 'Madayn Ibri Industrial City', '10 km2 gross, 3 km2 phase 1 (2024). Outside: collection tank, tankered', '#c724ff'),
    (426678, 2584304, 'Ibri IPP 1,539 MW + solar', 'construction camp. Outside: tankered', '#ffd23b'),
    (436225, 2574786, 'Police HQ + MOT centre', 'governmental, 19 CRT meters', '#ffffff'),
    (447900, 2569500, 'Ibri town workshops', '12 ha in the fabric. Stays in the shop allowance', '#c724ff'),
]

def render(name, extent, W, H, pts, title, show_plots_legend):
    ms = QgsMapSettings(); ms.setDestinationCrs(crs); ms.setOutputSize(QSize(W, H)); ms.setExtent(extent)
    ms.setBackgroundColor(QColor(20, 20, 20)); ms.setOutputDpi(120)
    ms.setLayers([sl, tl, bl, pl, sat])
    job = QgsMapRendererParallelJob(ms); job.start(); job.waitForFinished()
    img = job.renderedImage()
    ext = ms.extent()
    def px(E, N):
        return QPointF((E - ext.xMinimum()) / ext.width() * W, (ext.yMaximum() - N) / ext.height() * H)
    p = QPainter(img); p.setRenderHint(QPainter.Antialiasing)
    fS = QFont('Arial', 9); fB = QFont('Arial', 10, QFont.Bold); fT = QFont('Arial', 15, QFont.Bold)
    # markers + annotation boxes
    placed = []
    for i, (E, N, lab, note, col) in enumerate(pts):
        c = px(E, N)
        if not (0 <= c.x() <= W and 0 <= c.y() <= H): continue
        p.setPen(QPen(QColor(col), 3)); p.setBrush(Qt.NoBrush); p.drawEllipse(c, 9, 9)
        p.setPen(QPen(QColor('#000000'), 1)); p.setBrush(QBrush(QColor(col))); p.drawEllipse(c, 4, 4)
        # box to the right, nudged to avoid overlaps
        p.setFont(fB); wl = p.fontMetrics().horizontalAdvance(lab); p.setFont(fS); wn = p.fontMetrics().horizontalAdvance(note)
        bw = max(wl, wn) + 14; bh = 40
        bx, by = c.x() + 16, c.y() - bh / 2
        if bx + bw > W - 10: bx = c.x() - 16 - bw
        for _ in range(12):
            r = QRectF(bx, by, bw, bh)
            if not any(r.intersects(q) for q in placed): break
            by += bh + 4
        r = QRectF(bx, by, bw, bh); placed.append(r)
        p.setPen(QPen(QColor(col), 1.5)); p.setBrush(QBrush(QColor(0, 0, 0, 175))); p.drawRoundedRect(r, 4, 4)
        p.drawLine(c, QPointF(bx if bx > c.x() else bx + bw, by + bh / 2))
        p.setPen(QColor('#ffffff')); p.setFont(fB); p.drawText(QPointF(bx + 7, by + 16), lab)
        p.setFont(fS); p.setPen(QColor('#e8e8e8')); p.drawText(QPointF(bx + 7, by + 32), note)
    # title
    p.setFont(fT); p.setPen(QColor('#ffffff')); p.setBrush(QBrush(QColor(0, 0, 0, 170)))
    tw = p.fontMetrics().horizontalAdvance(title) + 20; p.drawRect(QRectF(10, 10, tw, 32)); p.drawText(QPointF(20, 33), title)
    # legend
    items = [('white line', 'project boundary 531 km2', '#ffffff'), ('cyan dash', 'W13 test area 5.5 km2', '#00e5ff'),
             ('purple', 'industrial (OSM footprint)', '#c724ff'), ('green', 'military (OSM footprint)', '#a3ff3b'),
             ('blue', 'wastewater plant', '#00b7ff'), ('orange', 'hotel', '#ff9d00')]
    if show_plots_legend:
        items += [('', 'MoH plots (7 Sept file):', None)] + [('', k, v) for k, v in pal.items()]
    lh = 18; lw = 250; lx, ly = 10, H - 10 - (len(items) * lh + 12)
    p.setPen(QPen(QColor('#ffffff'), 1)); p.setBrush(QBrush(QColor(0, 0, 0, 175))); p.drawRect(QRectF(lx, ly, lw, len(items) * lh + 12))
    p.setFont(fS)
    for i, (_, txt, col) in enumerate(items):
        y = ly + 8 + i * lh
        if col: p.setPen(QPen(QColor(col), 1)); p.setBrush(QBrush(QColor(col))); p.drawRect(QRectF(lx + 8, y + 3, 14, 10))
        p.setPen(QColor('#ffffff')); p.drawText(QPointF(lx + 28, y + 12), txt)
    # scale bar
    km = 5 if ext.width() > 20000 else 1
    sb = km * 1000 / ext.width() * W; sx, sy = W - 20 - sb, H - 24
    p.setPen(QPen(QColor('#ffffff'), 3)); p.drawLine(QPointF(sx, sy), QPointF(sx + sb, sy))
    p.setFont(fB); p.drawText(QPointF(sx, sy - 6), f'{km} km')
    p.end()
    out = f"{OUT}/{name}.png"; img.save(out); print('saved', out, W, H)

# map 1: whole boundary + outside sites
render('W14_identified_projects_overview', QgsRectangle(421000, 2551500, 481000, 2588500), 3000, 1850, PTS,
       'Identified projects and special consumption, whole boundary (9 Sept 2026)', True)
# map 2: the town
render('W14_identified_projects_town', QgsRectangle(439000, 2559000, 459000, 2575500), 3000, 2475, PTS,
       'Identified projects, Ibri town, with MoH plots by class', True)
