"""W18 QGIS project of the plot flows (engineer, 2026-11-17): the plot layer 2026-2100 filled by average flow in a blue
gradient (higher flow darker; no flow = no fill, so the plots kept out stay empty), the plot outline coloured by the
existing plot's land use in the planning convention (APA LBCS function colours: residential yellow, mixed orange,
commercial red, government/institutional blue, industrial purple, agricultural green), proposed plots outlined light
grey. Flow layers for 2031, 2056 (shown), 2071 and 2100 in a group where only one shows at a time. Built headless, so
the engineer's open QGIS session is not touched.
Run: "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" qgis_plot_flows_project.py
Writes qgis/W18_plot_flows.qgz (relative paths) and img/qgis_plot_flows_preview_<settlement>.png."""
import os, sys
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsGraduatedSymbolRenderer, QgsRendererRange, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsFillSymbol, QgsSingleSymbolRenderer, QgsMapSettings, QgsMapRendererParallelJob, QgsRectangle,
                       QgsLayerTreeGroup)
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtCore import QSize

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
PLOTS = os.path.join(W18, "gis", "W18_plots_2026_2100.shp")
SETTLE = os.path.join(W18, "gis", "W18_settlements_2026_2100.shp")   # W18 settlement layer (py/settlements_2100.py)
OUT = os.path.join(W18, "qgis", "W18_plot_flows.qgz")
os.makedirs(os.path.dirname(OUT), exist_ok=True)

qgs = QgsApplication([], False); qgs.initQgis()
prj = QgsProject.instance(); prj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
prj.setTitle("W18 plot flows (NWS basis, growth rule of 2026-11-17)")
root = prj.layerTreeRoot()

BREAKS = [(0.0, 0.25), (0.25, 0.5), (0.5, 1), (1, 2), (2, 4), (4, 8), (8, 1000)]
BLUES = ["#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#3182bd", "#08519c", "#08306b"]
LABELS = ["up to 0.25", "0.25 to 0.5", "0.5 to 1", "1 to 2", "2 to 4", "4 to 8", "over 8"]
LBCS = [("Residential", "#f2c500", "Residential"), ("Residential-Commercial", "#ff8c00", "Mixed residential-commercial"),
        ("Commercial", "#e31a1c", "Commercial"), ("Government", "#1f3fff", "Government / institutional"),
        ("Industrial", "#7b2cbf", "Industrial"), ("Agricultural", "#2ca02c", "Agricultural")]


def plots(name, subset=""):
    lyr = QgsVectorLayer(PLOTS, name, "ogr"); assert lyr.isValid(), PLOTS
    if subset: lyr.setSubsetString(subset)
    return lyr


def flow_layer(year):
    lyr = plots(f"Average flow {year}, m³/d per plot", f'"Q_{year}" > 0')   # no flow: not drawn, so the plot stays empty
    ranges = []
    for (lo, hi), c, lab in zip(BREAKS, BLUES, LABELS):
        sym = QgsFillSymbol.createSimple({"color": c, "outline_style": "no"})
        ranges.append(QgsRendererRange(lo, hi, sym, lab))
    lyr.setRenderer(QgsGraduatedSymbolRenderer(f"Q_{year}", ranges))
    return lyr


# outlines on top, flow beneath, basemap at the bottom
grp = root.addGroup("W18 plots")
ex = plots("Outline: existing plot, by land use", "\"STATUS\" = 'Existing'")
cats = []
for val, col, lab in LBCS:
    sym = QgsFillSymbol.createSimple({"style": "no", "outline_color": col, "outline_width": "0.45", "outline_width_unit": "MM"})
    cats.append(QgsRendererCategory(val, sym, lab))
other = QgsFillSymbol.createSimple({"style": "no", "outline_color": "#636363", "outline_width": "0.45", "outline_width_unit": "MM"})
cats.append(QgsRendererCategory("", other, "Other / not classified"))
ex.setRenderer(QgsCategorizedSymbolRenderer("LANDUSE", cats))
prop = plots("Outline: proposed plot", "\"STATUS\" = 'Future'")
prop.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
    {"style": "no", "outline_color": "#c8c8c8", "outline_width": "0.2", "outline_width_unit": "MM"})))
st = QgsVectorLayer(SETTLE, "Settlement boundary", "ogr"); assert st.isValid()
st.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple(
    {"style": "no", "outline_color": "#000000", "outline_width": "0.5", "outline_style": "dash", "outline_width_unit": "MM"})))
for l in (st, ex, prop):
    prj.addMapLayer(l, False); grp.addLayer(l)
fgrp = grp.addGroup("Average flow per plot (pick one year)")
fgrp.setIsMutuallyExclusive(True)
flows = {}
for y in (2031, 2056, 2071, 2100):
    flows[y] = flow_layer(y); prj.addMapLayer(flows[y], False); fgrp.addLayer(flows[y])
for y, l in flows.items():
    root.findLayer(l.id()).setItemVisibilityChecked(y == 2056)
fgrp.setIsMutuallyExclusive(True, 1)        # 2056 is the second child
gs = QgsRasterLayer("type=xyz&url=https://mt1.google.com/vt/lyrs%3Dy%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=20&zmin=0",
                    "Google satellite hybrid (30 %)", "wms")
if gs.isValid():
    gs.renderer().setOpacity(0.3); prj.addMapLayer(gs, False); root.addLayer(gs)
else:
    print("basemap not added (no XYZ provider)")

prj.writeEntryBool("Paths", "/Absolute", False)
assert prj.write(OUT), OUT
print("written", OUT)

# previews without the basemap (no tile download), to read the result
for s in ("IBRI", "BAT"):
    ms = QgsMapSettings(); ms.setDestinationCrs(prj.crs())
    ms.setLayers([st, ex, prop, flows[2056]])
    sub = QgsVectorLayer(PLOTS, "x", "ogr"); sub.setSubsetString(f"\"SETTLE\" ILIKE '{s}%' AND \"STATUS\" = 'Existing'")
    assert sub.featureCount() > 0, s
    xs, ys = zip(*[(f.geometry().centroid().asPoint().x(), f.geometry().centroid().asPoint().y()) for f in sub.getFeatures()])
    cx, cy = sorted(xs)[len(xs) // 2], sorted(ys)[len(ys) // 2]   # the median existing plot: the town, not the stragglers
    w = 1200 if s == "IBRI" else 900
    ms.setExtent(QgsRectangle(cx - w, cy - w * 0.7, cx + w, cy + w * 0.7))
    ms.setOutputSize(QSize(2400, 1680)); ms.setBackgroundColor(QColor("white"))
    job = QgsMapRendererParallelJob(ms); job.start(); job.waitForFinished()
    f = os.path.join(W18, "img", f"qgis_plot_flows_preview_{s}.png"); job.renderedImage().save(f); print("preview", f)
qgs.exitQgis()
