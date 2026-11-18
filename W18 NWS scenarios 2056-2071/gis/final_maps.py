"""W18 final design: the QGIS project of the four scenarios and three design years, and the report maps (2056, the base
design year) on the frame every report map uses (template_report_A3.qpt, through gis/make_w17_project.py):
  overview      the pumping systems: the sewers of each pump's system in one colour, the pumps, lifts and plant inlets;
  zones         the sewers by the plant they drain to, every station labelled with its depth;
  network       the sewers by plant and size, the stations labelled with depth, duty and head, the force mains (no arrow);
  depth         the depth of the sewers to invert, the station depths, the deepest manhole of every run over 12 m;
  selfcleansing the velocity class of every sewer above DN200 at the 2031 peak, with the 2036 check; the stations
                (no gravity-join marker, no force main - engineer, 2026-11-18).
Labels sized by the map scale, manholes with the engineer's style (qgis/styles/manholes_depth.qml), force mains and
sewers carry a small arrow in the direction of flow in the project, from 1:15,000 in (none on the printed maps).
Runs in the standalone QGIS python:  & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" final_maps.py [--no-render]
Writes results/final_0.75pc_SC1-SC4/qgis/Ibri_sewer_concept_design.qgz and report_final/img/*.png."""
import json, os, sys, tempfile
sys.stdout.reconfigure(line_buffering=True)
from qgis.core import (Qgis, QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem,
                       QgsRectangle, QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutItemLabel, QgsLayoutExporter,
                       QgsLayoutSize, QgsLayoutPoint, QgsTextFormat, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsSingleSymbolRenderer, QgsLineSymbol, QgsMarkerSymbol, QgsProperty, QgsSymbolLayer,
                       QgsGeometryGeneratorSymbolLayer, QgsMarkerLineSymbolLayer, QgsSimpleMarkerSymbolLayer,
                       QgsPalLayerSettings, QgsVectorLayerSimpleLabeling, QgsFeature, QgsGeometry)
from qgis.PyQt.QtGui import QColor, QFont

HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import make_w17_project as M
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
PROJECT = os.path.join(R, "qgis", "Ibri_sewer_concept_design.qgz")
IMG = os.path.join(W18, "report_final", "img")
BND = os.path.join(W18, "..", "W17", "Options 2026-10", "01_Boundaries", "Project_boundary_updated.shp")
STL = os.path.join(HERE, "W18_settlements_2026_2100.shp")
MH_QML = os.path.join(W18, "qgis", "styles", "manholes_depth.qml")
SUBTITLE = "Ibri Sewer, TE Networks and STP — Concept Design Report | Renardet 2621"
RENDER = "--no-render" not in sys.argv
SCEN = {"SC1": "SC1, STP-1 only", "SC2": "SC2, STP-2 only", "SC3": "SC3, STP-1 and STP-5", "SC4": "SC4, STP-2 and STP-5"}
YEARS, BASE = ["2051", "2056", "2061"], "2056"
LABEL_SIZE = "clamp(7, 8*25000/@map_scale, 36)"
PLANT_COLOUR = {"STP-1": "#2E75B6", "STP-5": "#C0504D", "STP-2": "#ED7D31"}
SYS_COLOUR = ["#e6194b", "#3cb44b", "#e0b400", "#4363d8", "#f58231", "#911eb4", "#46f0f0", "#f032e6", "#bcf60c",
              "#008080", "#6a3d9a", "#9a6324", "#800000", "#00c08b", "#808000"]
SC = [("DN200 (rule: above DN200 only)", "#9e9e9e", "DN200, not checked (rule: above DN200 only)"),
      ("Above DN200, 0.75 m/s as laid", "#1a9850", "Above DN200, 0.75 m/s at the design gradient"),
      ("Steepened up to 0.30 %", "#fdd49e", "Steepened, up to 0.30 %"),
      ("Steepened 0.30 to 0.50 %", "#fc8d59", "Steepened, 0.30 to 0.50 %"),
      ("Steepened 0.50 to 0.75 %", "#d7301f", "Steepened, 0.50 to 0.75 %"),
      ("Under 0.75 m/s in 2031, reaches it by 2036", "#c2a5cf", "Under 0.75 m/s in 2031, reaches it in 2036"),
      ("Under 0.75 m/s in 2031 and in 2036", "#7b3294", "Under 0.75 m/s in 2031 and in 2036")]
KIND = [("plant inlet", "square", M.NAVY, 4.2, "Plant inlet pumping station"), ("pump", "circle", "#a61b1b", 2.6, "Pumping station"),
        ("lift", "triangle", "#1f3fff", 3.2, "Lift station")]


def scale_labels(l, expr=None):
    pal = QgsPalLayerSettings(l.labeling().settings()); tf = pal.format(); tf.setSize(8.0)
    b = tf.buffer(); b.setEnabled(True); b.setSize(0.8); tf.setBuffer(b); pal.setFormat(tf); pal.scaleVisibility = False
    props = pal.dataDefinedProperties(); props.setProperty(QgsPalLayerSettings.Size, QgsProperty.fromExpression(LABEL_SIZE))
    pal.setDataDefinedProperties(props); l.setLabeling(QgsVectorLayerSimpleLabeling(pal)); l.setLabelsEnabled(True)


def arrow(colour, size=1.8):
    """An arrowhead at the centre of each line, along its drawn direction (lines are drawn with the flow), 1:15,000 in."""
    head = QgsSimpleMarkerSymbolLayer(Qgis.MarkerShape.ArrowHeadFilled, size); head.setColor(QColor(colour)); head.setStrokeColor(QColor(colour))
    ml = QgsMarkerLineSymbolLayer(True, 1.0); ml.setPlacements(Qgis.MarkerLinePlacement.CentralPoint); ml.setSubSymbol(QgsMarkerSymbol([head]))
    gen = QgsGeometryGeneratorSymbolLayer.create({"geometryModifier": "$geometry", "SymbolType": "Line"}); gen.setSubSymbol(QgsLineSymbol([ml]))
    gen.setDataDefinedProperty(QgsSymbolLayer.PropertyLayerEnabled, QgsProperty.fromExpression("@map_scale <= 15000"))
    return gen


def sym_line(colour, width=0.3, sized=True, arrows=False, style="solid"):
    s = M.line_symbol(colour, width, dd_width=sized)
    if style != "solid": s.symbolLayer(0).setPenStyle(Qgis.PenStyle.DashLine if hasattr(Qgis, "PenStyle") else 2)
    if arrows: s.appendSymbolLayer(arrow(colour))
    return s


def lyr(gpkg, layer, name, subset=""):
    l = QgsVectorLayer(f"{gpkg}|layername={layer}", name, "ogr")
    if not l.isValid(): return None
    if subset: l.setSubsetString(subset)
    return l


def style_stations(l, field):
    have = set(l.uniqueValues(l.fields().indexOf("kind")))
    l.setRenderer(QgsCategorizedSymbolRenderer("kind", [QgsRendererCategory(k, QgsMarkerSymbol.createSimple(
        {"name": shp, "color": c, "outline_color": "#ffffff", "outline_width": "0.35", "size": str(sz)}), lab) for k, shp, c, sz, lab in KIND if k in have]))
    M.label(l, f'"{field}"', size=6.0, colour="#1a1a1a", bold=True, priority=10, dist=0.8); scale_labels(l)


def style_force_mains(l, arrows):
    s = QgsLineSymbol.createSimple({"color": "#a61b1b", "width": "0.4", "line_style": "dash", "capstyle": "round"})
    if arrows: s.appendSymbolLayer(arrow("#a61b1b", 2.0))
    l.setRenderer(QgsSingleSymbolRenderer(s)); l.setName("Force main")


def make_map(proj, google, name, title, stack, legend_layers, ext, rows, out_png, test_layers):
    lay = M.clone(proj, name); mapitem = legend = None
    for it in lay.items():
        if isinstance(it, QgsLayoutItemMap):
            it.setLayers(stack + [google]); it.setKeepLayerSet(True); it.zoomToExtent(ext); mapitem = it
        elif isinstance(it, QgsLayoutItemLabel):
            t = it.text()
            if t.startswith("Ibri Sewer"):
                it.setText(SUBTITLE); it.attemptResize(QgsLayoutSize(230, 4.5, M.UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 9.6, M.UNIT_MM))
            elif t and not t.startswith("N"):
                it.setText(title); it.attemptResize(QgsLayoutSize(270, 6.5, M.UNIT_MM)); it.attemptMove(QgsLayoutPoint(8, 2.8, M.UNIT_MM))
        elif isinstance(it, QgsLayoutItemLegend):
            legend = it
    box = M.fill_box(lay, rows, width=92.0)
    if legend is not None:
        legend.setLinkedMap(mapitem); legend.setAutoUpdateModel(False)
        legend.setBackgroundEnabled(True); legend.setBackgroundColor(QColor(255, 255, 255, M.LEGEND_ALPHA)); legend.setWrapString("~")
        grp = legend.model().rootGroup()
        for ch in list(grp.children()): grp.removeChildNode(ch)
        for l, show_title in legend_layers:
            node = grp.addLayer(l)
            if not show_title: node.setCustomProperty("legend/title-style", "hidden")
        legend.setTitle(""); legend.setResizeToContents(True); legend.adjustBoxSize()
        tmp = QgsLayoutExporter(lay); ts = QgsLayoutExporter.ImageExportSettings(); ts.dpi = 25; mapitem.setLayers(stack)
        tmp.exportToImage(os.path.join(tempfile.gettempdir(), "final_legend_probe.png"), ts)
        sz = legend.sizeWithUnits(); mp, ms = mapitem.positionWithUnits(), mapitem.sizeWithUnits()
        legend.attemptMove(QgsLayoutPoint(mp.x() + 3.0, mp.y() + ms.height() - sz.height() - 3.0, M.UNIT_MM))
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
        res = exp.exportToImage(out_png, s); print("   ", os.path.basename(out_png), "ok" if res == QgsLayoutExporter.Success else f"FAILED {res}")
        proj.removeMapLayer(bg.id())
    mapitem.setLayers(stack + [google])


f1 = lambda v: f"{v:,.1f}"
f0 = lambda v: f"{v:,.0f}"


def build():
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); proj.clear(); proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    proj.setTitle("Ibri Sewer, TE Networks and STP: concept design of the sewer network, scenarios SC1 to SC4")
    proj.writeEntry("Paths", "/Absolute", False); root = proj.layerTreeRoot()
    os.makedirs(IMG, exist_ok=True); os.makedirs(os.path.dirname(PROJECT), exist_ok=True)

    def add(group, l, visible=True):
        if l is None: return None
        proj.addMapLayer(l, False); n = group.addLayer(l); n.setItemVisibilityChecked(visible); n.setExpanded(False); return l

    base = root.addGroup("Base")
    bnd = M.vec(BND, "Project boundary"); M.style_boundary(bnd); add(base, bnd)
    stl = M.vec(STL, "Settlement boundary"); M.style_settlements(stl); add(base, stl)
    google = QgsRasterLayer(M.GOOGLE, "Satellite image (Google)", "wms"); google.setOpacity(0.3); proj.addMapLayer(google, False)
    sizes = M.size_legend_layer(); proj.addMapLayer(sizes, False)
    ext = QgsRectangle(bnd.extent()); ext.scale(1.04)
    bline = QgsVectorLayer("LineString?crs=EPSG:32640", "boundary line", "memory"); feats = []
    for f in bnd.getFeatures():
        g = f.geometry()
        for part in (g.asMultiPolygon() if g.isMultipart() else [g.asPolygon()]):
            for ring in part:
                nf = QgsFeature(); nf.setGeometry(QgsGeometry.fromPolylineXY(ring)); feats.append(nf)
    bline.dataProvider().addFeatures(feats); bline.updateExtents()

    first = True
    for sc in ("SC1", "SC2", "SC3", "SC4"):
        gs = root.addGroup(SCEN[sc]); gs.setExpanded(sc == "SC1"); gs.setItemVisibilityChecked(sc == "SC1")
        for y in YEARS:
            case = f"{sc}-{y}"; gpkg = os.path.join(R, case, "products", "map.gpkg")
            Q = json.load(open(os.path.join(R, case, "products", "quantities.json")))
            Sp = json.load(open(os.path.join(R, case, "split", f"summary_{case}.json")))
            g = gs.addGroup(f"{sc} designed for {y}"); g.setExpanded(False); g.setItemVisibilityChecked(y == BASE)
            st = lyr(gpkg, "stations", "Stations: name and depth"); style_stations(st, "map_label")
            fm = lyr(gpkg, "force_mains", "Force main"); style_force_mains(fm, True)
            mh = lyr(gpkg, "manholes", "Manholes, depth (m)"); mh.loadNamedStyle(MH_QML)
            vel = lyr(gpkg, "pipes", "Sewers: self-cleansing at the 2031 peak")
            have = set(vel.uniqueValues(vel.fields().indexOf("sc_class")))
            vel.setRenderer(QgsCategorizedSymbolRenderer("sc_class", [QgsRendererCategory(v, sym_line(c, arrows=True), lab) for v, c, lab in SC if v in have]))
            plants = sorted({v["stp"] for v in Q["plants"].values()})
            zs = lyr(gpkg, "pipes", "Sewers by plant and size")
            zs.setRenderer(QgsCategorizedSymbolRenderer("stp", [QgsRendererCategory(p, sym_line(PLANT_COLOUR.get(p, "#555555")), f"To {p}") for p in plants]))
            dp = lyr(gpkg, "pipes", "Depth to invert"); M.style_pipes_depth(dp)
            dr = lyr(gpkg, "deep_runs", "Deepest manhole of a run over 12 m")
            if dr is not None: M.style_deep(dr); scale_labels(dr)
            for l, v in ((st, True), (fm, True), (mh, True), (vel, True), (zs, False), (dp, False), (dr, False)): add(g, l, v)
            if y != BASE: continue
            # ------------------------------------------------------------ the report maps, 2056
            S = json.load(open(os.path.join(R, case, "products", "quantities.json")))
            prow = [(f"{v['stp']} (inlet {p}), {y} average", f"{f0(v['avg_m3d'][y])} m³/d, inlet {v['inlet_depth_m']:.1f} m deep") for p, v in S["plants"].items()]
            st_only = lambda: [x for x in (st,) if x]
            stp = lyr(gpkg, "stations", "Stations"); style_stations(stp, "map_label"); proj.addMapLayer(stp, False)
            sdu = lyr(gpkg, "stations", "Stations"); style_stations(sdu, "duty_label"); proj.addMapLayer(sdu, False)
            fmp = lyr(gpkg, "force_mains", "Force main"); style_force_mains(fmp, False); proj.addMapLayer(fmp, False)
            z1 = lyr(gpkg, "pipes", "Sewers by plant")
            z1.setRenderer(QgsCategorizedSymbolRenderer("stp", [QgsRendererCategory(p, sym_line(PLANT_COLOUR.get(p, "#555555"), sized=False), f"To {p}") for p in plants]))
            proj.addMapLayer(z1, False)
            vp = lyr(gpkg, "pipes", "Sewers")
            vp.setRenderer(QgsCategorizedSymbolRenderer("sc_class", [QgsRendererCategory(v, sym_line(c), lab) for v, c, lab in SC if v in have]))
            proj.addMapLayer(vp, False)
            tag = f"{sc}_{y}"
            if first:
                first = False
                ov = lyr(gpkg, "pipes", "Sewers, one colour per pumping system")
                systems = sorted({s.split("L")[0] for s in ov.uniqueValues(ov.fields().indexOf("section"))}, key=lambda s: int(s[1:]))
                ov.setRenderer(QgsCategorizedSymbolRenderer('regexp_substr("section", \'^P[0-9]+\')',
                               [QgsRendererCategory(s, sym_line(SYS_COLOUR[i % len(SYS_COLOUR)], 0.35, sized=False), s) for i, s in enumerate(systems)]))
                proj.addMapLayer(ov, False)
                leg = M.memory_line("Sewer, one colour~per pumping system", "#4363d8"); proj.addMapLayer(leg, False)
                print("overview")
                make_map(proj, google, "Pumping systems", f"The sewer network: {len(systems)} pumping systems, pumps and lifts",
                         [stp, ov, stl, bnd], [(stp, False), (leg, False), (stl, False), (bnd, False)], ext,
                         [("Pumping systems", f"{len(systems)}"), ("Pumps / lifts", f"{S['pumps']} / {S['lifts']}"),
                          ("Sewer", f"{f0(S['sewer_km'])} km"), ("Manholes", f0(S["manholes"]))],
                         os.path.join(IMG, "map_pumping_systems.png"), [ov, stp, bline])
            print(case)
            make_map(proj, google, f"{sc} zones", f"{SCEN[sc]}: sewers by the plant they drain to ({y})",
                     [stp, fmp, z1, stl, bnd], [(stp, False), (z1, False), (fmp, False), (bnd, False)], ext, prow,
                     os.path.join(IMG, f"map_{tag}_zones.png"), [z1, stp, bline])
            make_map(proj, google, f"{sc} network", f"{SCEN[sc]}: sewers, pumping stations and lifts ({y})",
                     [sdu, fmp, zs, stl, bnd], [(sdu, False), (zs, False), (sizes, True), (fmp, False), (bnd, False)], ext,
                     prow + [("Sewers", f"{f0(S['sewer_km'])} km"), ("Pumping stations / lifts", f"{S['pumps']} / {S['lifts']}"),
                             ("Force mains", f"{f1(S['force_main_km'])} km"), ("Network pumping duty", f"{f0(S['kw_network'])} kW"),
                             ("Pumping energy 2031 / " + y, f"{f0(S['mwh_2031'])} / {f0(S['mwh_design'])} MWh/yr")],
                     os.path.join(IMG, f"map_{tag}_network.png"), [zs, sdu, bline])
            km = S["km_by_depth"]
            make_map(proj, google, f"{sc} depth", f"{SCEN[sc]}: depth of the sewers to invert ({y})",
                     [x for x in (stp, dr, dp, bnd) if x], [(dp, False)] + ([(dr, False)] if dr else []) + [(stp, False), (bnd, False)], ext,
                     [(b if i else "Sewer up to 3 m deep", f"{f1(km.get(b, 0))} km") for i, b in enumerate(["up to 3 m", "3 to 6 m", "6 to 9 m", "9 to 12 m", "12 to 15 m", "over 15 m"])]
                     + [("Deepest manhole", f"{S['deepest']['depth']:.1f} m")], os.path.join(IMG, f"map_{tag}_depth.png"), [dp, stp, bline])
            kb = S["km_big"]
            make_map(proj, google, f"{sc} self-cleansing", f"{SCEN[sc]}: self-cleansing at the 2031 peak ({y})",
                     [stp, vp, stl, bnd], [(stp, False), (vp, False), (sizes, True), (stl, False)], ext,
                     [("Gradient limit", "0.75 % (one gradient per street run)"), ("Sewers above DN200", f"{f1(kb)} km"),
                      ("Steepened", f"{f1(Sp['km_steepened'])} km"),
                      ("Under 0.75 m/s at the 2031 peak", f"{f1(S['km_big_under075_2031'])} km ({S['km_big_under075_2031'] / kb * 100:.1f} %)"),
                      ("   of which still under in 2036", f"{f1(S['km_big_under075_2036'])} km ({S['km_big_under075_2036'] / kb * 100:.1f} %)"),
                      ("Highest velocity, design peak", f"{Sp['v2056_max']:.2f} m/s"),
                      ("Pumping stations / lifts", f"{S['pumps']} / {S['lifts']}"),
                      ("Manholes deeper than 12 m", f"{S['manholes_by_depth'].get('12 to 15 m', 0) + S['manholes_by_depth'].get('over 15 m', 0)}"),
                      ("Deepest manhole", f"{S['deepest']['depth']:.1f} m")],
                     os.path.join(IMG, f"map_{tag}_selfcleansing.png"), [vp, stp, bline])
    root.addLayer(google)
    assert proj.write(PROJECT), PROJECT
    print("wrote", PROJECT, "|", len(proj.mapLayers()), "layers |", len(proj.layoutManager().layouts()), "layouts")
    app.exitQgis()


if __name__ == "__main__":
    build()
