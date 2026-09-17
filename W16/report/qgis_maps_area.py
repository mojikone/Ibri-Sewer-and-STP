"""Map figures of the study-area section (1.2) of the Concept Design Report, Revision 3.

Run inside QGIS with the project stp2.qgz open (through report_basis/qgis_direct.py):

    import qgis_maps_area as qa; qa.build()            # or qa.build(["A01_topography"])

Every figure is a clone of the template layout, kept in the project as "RPT A..", and is
exported to report/img. The layers are copies styled here; the engineer's own layers and their
styles are not touched. The numbers in the data boxes come from
analysis/study_area/study_area_stats.json, the file the text reads too.

    A01_topography     terrain 0.5 m: hillshade, ground level tint, wadis, the existing STP
    A02_roads          road centrelines as supplied, by the class code they carry (StrCls)
    A03..A06_hazard    flood hazard for 10, 25, 50 and 100 years, Oman Flood Mapping project (MAFWR),
                       Australian hazard classes H1 to H6, the engineer's colours, 50 % transparent

The main pipe is not shown on any of them: it is not client data (engineer, 2026-09-17).
"""
import json
import os
import sys

from qgis.core import (QgsProject, QgsVectorLayer, QgsRasterLayer, QgsLineSymbol, QgsCategorizedSymbolRenderer,
                       QgsRendererCategory, QgsGraduatedSymbolRenderer, QgsRendererRange, QgsPalettedRasterRenderer,
                       QgsHillshadeRenderer, QgsSingleBandGrayRenderer, QgsContrastEnhancement,
                       QgsSingleBandPseudoColorRenderer, QgsColorRampShader, QgsRasterShader,
                       QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutItemLabel, QgsLayoutExporter, QgsLayoutSize,
                       QgsLayoutPoint, QgsUnitTypes, QgsRectangle, QgsMapLayerLegendUtils,
                       QgsColorRampLegendNodeSettings, QgsBasicNumericFormat, QgsSimpleLineSymbolLayer,
                       QgsFillSymbol, QgsSingleSymbolRenderer, QgsInvertedPolygonRenderer)
from qgis.PyQt.QtCore import QSizeF, Qt
from qgis.PyQt.QtGui import QColor

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import qgis_maps as qm  # noqa: E402

W16 = os.path.dirname(HERE)
REPO = os.path.dirname(W16)
HYD = os.path.dirname(REPO)
IMG = os.path.join(HERE, "img")
STATS = os.path.join(W16, "analysis", "study_area", "study_area_stats.json")
UNIT_MM = QgsUnitTypes.LayoutMillimeters

TERRAIN = os.path.join(HYD, "Terrain", "Sat_0p5m", "IBRI_0p5_clip.tif")
# the same terrain thinned to 2 m for the meeting folder draws faster and smoother at this scale
TERRAIN_2M = os.path.join(W16, "Meeting 2026-09-16", "07_Terrain", "IBRI_terrain_2m.tif")
HILLSHADE_2M = os.path.join(W16, "Meeting 2026-09-16", "07_Terrain", "IBRI_terrain_2m_hillshade.tif")
ROADS = os.path.join(HYD, "SHP", "Road centerline 2", "Road_Centercline.shp")
STREAMS = os.path.join(HYD, "SHP", "Streams", "Streams NSA 2m project boundary.shp")
HAZARD_DIRS = [os.path.join(W16, "Meeting 2026-09-16", "04_Hydrology"),
               r"\\fileserver-\Works\2331 Flood Hazard Maps for Muscat-Dhofar-Musandam_MWR\06-WORKING\04-Hydraulic"
               r"\05-Hazard_Risk\FloodHazard_OM_20260608\Project2\2.3-Area3\04 Lekhuwair"]

# Australian flood hazard classes (AIDR Guideline 7-3, 2017), the engineer's colours in QGIS
HAZARD = [(1, "#0071ff", "H1  generally safe"),
          (2, "#47c4ff", "H2  unsafe for small vehicles"),
          (3, "#00fff9", "H3  unsafe for vehicles, children, the elderly"),
          (4, "#0eff00", "H4  unsafe for people and vehicles"),
          (5, "#fff200", "H5  buildings vulnerable to damage"),
          (6, "#f41f1f", "H6  buildings vulnerable to failure")]
# the road class code as supplied; the engineer's colours, widths thinned for a sheet at 1:170,000
ROAD_CLASSES = [("05", "#abdda4", 0.16, 0), ("04", "#ffffbf", 0.45, 1), ("02", "#fdae61", 0.60, 2), ("01", "#d7191c", 0.70, 3)]
# ground level tint, stretched over the range the plots lie in so the fall to the STP reads
TINT = [(300, "#FFFFD4"), (340, "#FEE391"), (380, "#FEC44F"), (420, "#FE9929"), (460, "#D95F0E"), (500, "#993404"), (540, "#4A1A02")]

_L = {}


def _stats():
    with open(STATS, encoding="utf-8") as fh:
        return json.load(fh)


def _add(layer):
    if not layer.isValid():
        raise RuntimeError("layer not valid: " + layer.source())
    QgsProject.instance().addMapLayer(layer, False)      # not in the layer tree
    _L[layer.name()] = layer
    return layer


def terrain_layers():
    if "Ground level" in _L:
        return [_L["Wadi, by stream order"], _L["Ground level"], _L["Hillshade"]]
    src = TERRAIN_2M if os.path.exists(TERRAIN_2M) else TERRAIN
    if os.path.exists(HILLSHADE_2M):
        hs = QgsRasterLayer(HILLSHADE_2M, "Hillshade")
        g = QgsSingleBandGrayRenderer(hs.dataProvider(), 1)
        ce = QgsContrastEnhancement(hs.dataProvider().dataType(1))
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.StretchToMinimumMaximum)
        ce.setMinimumValue(60); ce.setMaximumValue(255)
        g.setContrastEnhancement(ce); hs.setRenderer(g)
    else:
        hs = QgsRasterLayer(src, "Hillshade")
        hs.setRenderer(QgsHillshadeRenderer(hs.dataProvider(), 1, 315, 45))
    _add(hs)

    tint = QgsRasterLayer(src, "Ground level")
    fn = QgsColorRampShader(TINT[0][0], TINT[-1][0])
    fn.setColorRampType(QgsColorRampShader.Interpolated)
    fn.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), f"{v} m") for v, c in TINT])
    st = QgsColorRampLegendNodeSettings()
    fmt = QgsBasicNumericFormat(); fmt.setNumberDecimalPlaces(0); fmt.setShowTrailingZeros(False)
    st.setNumericFormat(fmt); st.setMinimumLabel(f"{TINT[0][0]} m and below"); st.setMaximumLabel(f"{TINT[-1][0]} m and above")
    fn.setLegendSettings(st)
    sh = QgsRasterShader(); sh.setRasterShaderFunction(fn)
    r = QgsSingleBandPseudoColorRenderer(tint.dataProvider(), 1, sh)
    r.setOpacity(0.55)
    tint.setRenderer(r); _add(tint)

    w = QgsVectorLayer(STREAMS, "Wadi, by stream order", "ogr")
    w.setSubsetString('"STRM_VAL" >= 3')                  # the first two orders are hairlines at this scale
    rng = []
    for order, width in ((3, 0.16), (4, 0.28), (5, 0.42), (6, 0.58), (7, 0.75)):
        sym = QgsLineSymbol.createSimple({"color": "#1F5FBF", "width": str(width), "width_unit": "MM", "capstyle": "round"})
        rng.append(QgsRendererRange(order - 0.5, order + 0.5, sym, f"order {order}"))
    w.setRenderer(QgsGraduatedSymbolRenderer("STRM_VAL", rng)); _add(w)
    return [w, tint, hs]


def road_layer():
    if "Road class, as supplied" in _L:
        return _L["Road class, as supplied"]
    rd = QgsVectorLayer(ROADS, "Road class, as supplied", "ogr")
    cats = []
    for code, colour, width, level in ROAD_CLASSES[::-1]:            # legend from class 01 down
        # the engineer's colour over a thin dark casing: the pale classes vanish on the imagery without it
        sym = QgsLineSymbol.createSimple({"color": "#3C3C3C", "width": str(width + 0.22), "width_unit": "MM", "capstyle": "round"})
        top = QgsSimpleLineSymbolLayer(QColor(colour), width); top.setWidthUnit(QgsUnitTypes.RenderMillimeters)
        top.setPenCapStyle(Qt.RoundCap)
        sym.appendSymbolLayer(top)
        casing = sym.symbolLayer(0); casing.setRenderingPass(2 * level)
        face = sym.symbolLayer(1); face.setRenderingPass(2 * level + 1)
        cats.append(QgsRendererCategory(code, sym, f"Class {code}"))
    r = QgsCategorizedSymbolRenderer("StrCls", cats)
    r.setUsingSymbolLevels(True)                                     # class 01 drawn over class 05
    rd.setRenderer(r)
    return _add(rd)


def hazard_layer(T):
    name = f"Flood hazard, {T}-year return period"
    if name in _L:
        return _L[name]
    path = None
    for folder in HAZARD_DIRS:
        p = os.path.join(folder, f"Hazard_T{T}y.tif")
        if os.path.exists(p):
            path = p; break
    if path is None:
        raise RuntimeError(f"Hazard_T{T}y.tif not found")
    hz = QgsRasterLayer(path, name)
    classes = [QgsPalettedRasterRenderer.Class(v, QColor(c), lab) for v, c, lab in HAZARD]
    r = QgsPalettedRasterRenderer(hz.dataProvider(), 1, classes)
    r.setOpacity(0.5)                                               # 50 % transparent, as the engineer's layer
    hz.setRenderer(r)
    return _add(hz)


def outside_veil():
    """The ground outside the project boundary under a white veil: the hazard model covers a rectangle far
    wider than the study area, and its straight edge would otherwise frame the figure."""
    if "outside" in _L:
        return _L["outside"]
    bnd = [l for l in QgsProject.instance().mapLayers().values() if l.name() == "Project Boundary updated"][0]
    v = QgsVectorLayer(bnd.source(), "outside", bnd.providerType())
    fill = QgsFillSymbol.createSimple({"color": "255,255,255,165", "outline_style": "no"})
    v.setRenderer(QgsInvertedPolygonRenderer(QgsSingleSymbolRenderer(fill)))
    return _add(v)


def _named(names):
    proj = QgsProject.instance(); out = []
    r2 = qm._r2_layers()
    for n in names:
        if n in r2:
            out.append(r2[n]); continue
        hit = [l for l in proj.mapLayers().values() if l.name() == n]
        if not hit:
            raise RuntimeError("layer not in the project: " + n)
        out.append(hit[0])
    return out


def _boxes():
    s = _stats(); g = s["ground"]; rd = s["roads"]
    top = max(g["settlements"], key=lambda r: r["z_med"])
    box = {
        "A01_topography": [("Terrain model", "0.5 m grid"), ("Ground at the plots", f"{g['z_p01']:.0f} to {g['z_p99']:.0f} m"),
                           ("Existing STP", f"{g['stp_ground']:.0f} m"), (f"Highest settlement, {top['name']}", f"{top['z_med']:.0f} m"),
                           ("Wadis shown", "stream order 3 and above")],
        "A02_roads": [("Road centrelines", f"{rd['total_km']:,.0f} km")] +
                     [(f"Class {c}", f"{rd['by_class_km'][c]:,.0f} km") for c in ("01", "02", "04", "05")] +
                     [("Source", "centrelines as supplied")],
    }
    for T in (10, 25, 50, 100):
        box[f"A{3 + (10, 25, 50, 100).index(T):02d}_hazard_T{T}"] = [
            ("Return period", f"{T} years"), ("Source", "Oman Flood Mapping, MAFWR"),
            ("Hazard classes", "Australian, H1 to H6"), ("Model grid", "3 m")]
    return box


FIGURES = {
    "A01_topography": ("Topography and drainage of the study area", "terrain"),
    "A02_roads": ("Road network of the study area", "roads"),
    "A03_hazard_T10": ("Flood hazard, 10-year return period", 10),
    "A04_hazard_T25": ("Flood hazard, 25-year return period", 25),
    "A05_hazard_T50": ("Flood hazard, 50-year return period", 50),
    "A06_hazard_T100": ("Flood hazard, 100-year return period", 100),
}
BOX_WIDTH = {"A01_topography": 76.0, "A02_roads": 66.0, "A03_hazard_T10": 72.0, "A04_hazard_T25": 72.0,
             "A05_hazard_T50": 72.0, "A06_hazard_T100": 72.0}


def _stack(kind):
    if kind == "terrain":
        w, tint, hs = terrain_layers()
        return _named(["Project Boundary updated", "STP location", "Settlement boundary"]) + [w, tint, hs]
    if kind == "roads":
        return _named(["Project Boundary updated", "Settlement boundary"]) + [road_layer()]
    return _named(["Project Boundary updated", "STP location", "Settlement boundary"]) + [outside_veil(), hazard_layer(kind)]


def build(keys=None, dpi=200, save=True):
    os.makedirs(IMG, exist_ok=True)
    proj = QgsProject.instance()
    bnd = [l for l in proj.mapLayers().values() if l.name() == "Project Boundary updated"][0]
    ext = QgsRectangle(bnd.extent()); ext.scale(1.06)
    boxes = _boxes(); bm = qm._basemap50(); made = []
    for key, (title, kind) in FIGURES.items():
        if keys and key not in keys:
            continue
        print(key)
        lay = qm._clone("RPT " + key)
        stack = _stack(kind) + ([bm] if bm else [])
        legends = []
        for it in lay.items():
            if isinstance(it, QgsLayoutItemMap):
                it.setLayers(stack); it.setKeepLayerSet(True); it.zoomToExtent(ext)
            elif isinstance(it, QgsLayoutItemLegend):
                it.setBackgroundEnabled(True); it.setBackgroundColor(QColor(255, 255, 255, 248)); legends.append(it)
            elif isinstance(it, QgsLayoutItemLabel):
                t = it.text()
                if t.startswith("Ibri Sewer"):
                    it.setText(qm.SUBTITLE); it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
                elif t and not t.startswith("N"):
                    it.setText(title); it.attemptResize(QgsLayoutSize(220, 6.5, UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))
        mapitem = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]
        for lg in legends:
            lg.setLinkedMap(mapitem); lg.setAutoUpdateModel(False)
            grp = lg.model().rootGroup()
            for ch in list(grp.children()):
                grp.removeChildNode(ch)
            for l in stack:
                if l is bm or l.name() in ("Hillshade", "outside"):
                    continue
                node = grp.addLayer(l)
                r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() == "categorizedSymbol":
                    node.setCustomProperty("legend/title-style", "hidden")
                if isinstance(l, QgsRasterLayer):
                    # a raster legend leads with "Band 1", which says nothing: keep the classes, drop that node
                    lg.model().refreshLayerLegend(node)
                    kids = lg.model().layerLegendNodes(node)
                    keep = [i for i, n in enumerate(kids) if type(n).__name__ != "QgsSimpleLegendNode"]
                    for i, n in enumerate(kids):
                        if type(n).__name__ == "QgsColorRampLegendNode":     # the ramp at a readable size
                            QgsMapLayerLegendUtils.setLegendNodeSymbolSize(node, i, QSizeF(7.0, 32.0))
                    if keep and len(keep) < len(kids):
                        QgsMapLayerLegendUtils.setLegendNodeOrder(node, keep)
                    lg.model().refreshLayerLegend(node)
            lg.setTitle(""); lg.setResizeToContents(True); lg.adjustBoxSize()
        qm._fill_box(lay, boxes[key], width=BOX_WIDTH.get(key))
        path = os.path.join(IMG, key + ".png")
        settings = QgsLayoutExporter.ImageExportSettings(); settings.dpi = dpi
        res = QgsLayoutExporter(lay).exportToImage(path, settings)
        made.append((key, res == QgsLayoutExporter.Success, path))
        print("   ", "ok" if res == QgsLayoutExporter.Success else "FAILED")
    if save:
        proj.write()                   # the layouts stay in the project
    return made
