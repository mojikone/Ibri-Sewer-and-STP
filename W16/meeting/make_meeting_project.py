"""Build the meeting's QGIS project from the files in W16/Meeting 2026-09-16, styled as in
stp2.qgz and as the report maps. Runs in the standalone QGIS python:

    & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" make_meeting_project.py

The folder is filled by make_meeting_folder.py (copies, raster clips, the styles exported
from the running stp2.qgz into _styles/). This script only assembles the project:
groups, layers with their QML, the labelled settlement copies, the overflow arrows from
routes.json, the basemap at 50 %, and a rendered check image.
"""
import json
import os
import sys

from qgis.core import (Qgis, QgsApplication, QgsCoordinateReferenceSystem, QgsCoordinateTransformContext, QgsFeature, QgsField,
                       QgsFields, QgsGeometry, QgsLayerTreeGroup, QgsMapRendererParallelJob, QgsMapSettings, QgsPalLayerSettings,
                       QgsPointXY, QgsProject, QgsProviderRegistry, QgsRasterLayer, QgsRectangle, QgsTextBufferSettings,
                       QgsTextFormat, QgsVectorFileWriter, QgsVectorLayer, QgsVectorLayerSimpleLabeling, QgsCategorizedSymbolRenderer,
                       QgsRendererCategory, QgsMarkerSymbol, QgsFillSymbol, QgsSimpleLineSymbolLayer, QgsLineSymbol)
from PyQt5.QtCore import QSize, QVariant
from PyQt5.QtGui import QColor

HERE = os.path.dirname(os.path.abspath(__file__))
M = os.path.join(os.path.dirname(HERE), "Meeting 2026-09-16")
ST = os.path.join(M, "_styles")
ROUTES = os.path.join(os.path.dirname(HERE), "report", "img", "routes.json")
PROJECT = os.path.join(M, "Ibri_meeting_2026-09-16.qgz")
GOOGLE = ("crs=EPSG:3857&format&http-header:referer=&type=xyz&url=https://www.google.cn/maps/vt?lyrs%3Ds@189%26gl%3Dcn%26x%3D%7Bx%7D%26y%3D%7By%7D%26z%3D%7Bz%7D&zmax=19&zmin=0")
NAVY = "#1F497D"


def qml(layer, name):
    p = os.path.join(ST, name + ".qml")
    if not os.path.exists(p):
        print("   no style:", name); return False
    msg, ok = layer.loadNamedStyle(p)
    if not ok:
        print("   style failed:", name, msg)
    layer.triggerRepaint(); return ok


def vec(rel, name, style=None, sub=None):
    src = os.path.join(M, rel) + (f"|layername={sub}" if sub else "")
    l = QgsVectorLayer(src, name, "ogr")
    if not l.isValid():
        print("   INVALID:", rel, sub); return None
    if style:
        qml(l, style)
    return l


def ras(rel, name, style=None):
    l = QgsRasterLayer(os.path.join(M, rel), name)
    if not l.isValid():
        print("   INVALID raster:", rel); return None
    if style:
        qml(l, style)
    return l


def label(layer, expr, size=7.5, colour=NAVY, bold=False, buffer=0.9):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True; pal.enabled = True
    pal.placement = Qgis.LabelPlacement.OverPoint if layer.geometryType() == 0 else Qgis.LabelPlacement.Horizontal
    tf = QgsTextFormat(); tf.setSize(size); tf.setColor(QColor(colour))
    f = tf.font(); f.setBold(bold); tf.setFont(f)
    b = QgsTextBufferSettings(); b.setEnabled(True); b.setSize(buffer); b.setColor(QColor("#FFFFFF")); tf.setBuffer(b)
    pal.setFormat(tf); pal.multilineAlign = Qgis.LabelMultiLineAlignment.Center
    layer.setLabelsEnabled(True); layer.setLabeling(QgsVectorLayerSimpleLabeling(pal))


def arrows_layer():
    """The overflow routes (people moved at saturation, 500 or more) as a line shapefile, from routes.json."""
    out = os.path.join(M, "02_Settlements", "Overflow_routes.shp")
    rj = json.load(open(ROUTES, encoding="utf-8"))
    fields = QgsFields(); fields.append(QgsField("people", QVariant.Double)); fields.append(QgsField("label", QVariant.String, len=80))
    opts = QgsVectorFileWriter.SaveVectorOptions(); opts.driverName = "ESRI Shapefile"; opts.fileEncoding = "UTF-8"
    w = QgsVectorFileWriter.create(out, fields, Qgis.WkbType.LineString, QgsCoordinateReferenceSystem("EPSG:32640"), QgsCoordinateTransformContext(), opts)
    n = 0
    for r in rj["routes"]:
        if r["people"] < 500:
            continue
        f = QgsFeature(fields); f.setGeometry(QgsGeometry.fromPolylineXY([QgsPointXY(r["x1"], r["y1"]), QgsPointXY(r["x2"], r["y2"])]))
        f.setAttributes([float(r["people"]), f"{r['donor_name']} to {r['receiver_name']}"]); w.addFeature(f); n += 1
    del w
    print("   overflow routes:", n)
    return "02_Settlements/Overflow_routes.shp"


def meters_style(l):
    cols = [("domestic", "Domestic", "#C0504D"), ("non_domestic", "Non-domestic", "#E5A32B"), ("government", "Governmental", "#3498DB"),
            ("agricultural", "Agricultural", "#4CAF50"), ("special", "Special consumption", "#9B59B6")]
    l.setRenderer(QgsCategorizedSymbolRenderer("GUD", [QgsRendererCategory(k, QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": c, "outline_color": "#ffffff", "outline_width": "0.15", "size": "1.4"}), lab) for k, lab, c in cols]))


def use_style(l):
    cols = [("Residential", "#FFE600"), ("Residential-Commercial", "#F5A742"), ("Commercial", "#E03C31"), ("Government", "#3498DB"),
            ("Agricultural", "#4CAF50"), ("Industrial", "#9B59B6"), ("Heritage", "#8d6e63")]
    cats = [QgsRendererCategory(k, QgsFillSymbol.createSimple({"color": c, "outline_style": "no"}), k) for k, c in cols]
    cats.append(QgsRendererCategory("Empty (unmetered)", QgsFillSymbol.createSimple({"style": "no", "outline_color": "#4a4a4a", "outline_width": "0.11", "outline_width_unit": "MM"}), "Empty (unmetered)"))
    l.setRenderer(QgsCategorizedSymbolRenderer("USE", cats))


def dashed(l, colour, width=0.6):
    sym = QgsLineSymbol.createSimple({"color": colour, "width": str(width), "line_style": "dash"})
    from qgis.core import QgsFillSymbol as _F
    fs = _F.createSimple({"style": "no", "outline_color": colour, "outline_width": str(width), "outline_style": "dash"})
    l.renderer().setSymbol(fs)


def build():
    app = QgsApplication([], False); app.initQgis()
    proj = QgsProject.instance(); proj.clear()
    proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    proj.setTitle("Ibri Sewer, TE Networks and STP: Design Basis, meeting of 16 September 2026")
    proj.writeEntry("Paths", "/Absolute", False)
    root = proj.layerTreeRoot()
    routes = arrows_layer()

    def group(name, expanded=True, checked=True):
        g = root.addGroup(name); g.setExpanded(expanded); g.setItemVisibilityChecked(checked); return g

    def add(g, layer, visible=True, expanded=False):
        if layer is None:
            return None
        proj.addMapLayer(layer, False); node = g.addLayer(layer); node.setItemVisibilityChecked(visible); node.setExpanded(expanded); return layer

    # ---- report maps: the styled copies asked for the meeting
    g = group("Report maps")
    s_people = vec("02_Settlements/Settlements.shp", "Settlements: people 2055 / at saturation", "Settlement_boundary_redrawn_as_a_partition")
    label(s_people, '''"NAME" || '\\n' || format_number("P2055", 0) || ' / ' || format_number("SAT_POP", 0)''', size=7.5, bold=True)
    add(g, s_people)
    s_flow = vec("02_Settlements/Settlements_full_W14.shp", "Settlements: flow 2055 / at saturation, m³/d (basis Fig. 16 style)", "Average_sewage_flow_at_saturation_2070_m_d")
    add(g, s_flow, visible=False)
    s_over = vec("02_Settlements/Settlements_full_W14.shp", "Capacity taken by overflow (concept Fig. 19)", "Capacity_taken_by_overflow")
    add(g, s_over, visible=False)
    ar = vec(routes, "Overflow, people moved at saturation (concept Fig. 19)", "Overflow_people")
    add(g, ar, visible=False)
    pq = vec("03_Plots_meters/Plots_full_W14.shp", "Average sewage flow of the plot at saturation, m³/d (concept Fig. 25)", "Average_sewage_flow_of_the_plot_at_saturation")
    add(g, pq, visible=False)
    ip = vec("10_Identified_projects/Identified_projects_footprints.shp", "Identified site, footprint (concept Fig. 26)", "Identified_site")
    add(g, ip, visible=False)
    ipp = vec("10_Identified_projects/Identified_project_sites.shp", "Identified project (concept Fig. 26)", "Identified_project")
    add(g, ipp, visible=False)
    fm = vec("03_Plots_meters/free_meters.shp", "The 126 meters more than 15 m from any plot (basis Fig. 3)", "Meter_more_than_15_m_from_any_plot")
    add(g, fm, visible=False)
    pu = vec("03_Plots_meters/Plots_full_W14.shp", "Use of the plot (basis Fig. 8)", "Use_of_the_plot")
    add(g, pu, visible=False)

    # ---- boundaries
    g = group("Boundaries")
    b_upd = vec("01_Boundaries/Project_boundary_updated.shp", "Project boundary, updated (531 km²)", "Project_Boundary_updated"); add(g, b_upd)
    b_rec = vec("01_Boundaries/Project_boundary_received.shp", "Project boundary, received (440 km²)")
    if b_rec:
        dashed(b_rec, "#C0504D", 0.6); add(g, b_rec)
    t_rec = vec("01_Boundaries/Settlement_boundaries_received.shp", "Settlement boundaries, received (Inception Report)", "Settlement_boundary_as_received_Inception_Report"); add(g, t_rec, visible=False)
    s_upd = vec("02_Settlements/Settlements.shp", "Settlements, updated (partition)", "Settlement_boundary_redrawn_as_a_partition")
    label(s_upd, '"NAME"', size=7, bold=False); add(g, s_upd, visible=False)

    # ---- plots and meters
    g = group("Plots and meters", expanded=False)
    pl = vec("03_Plots_meters/Plots.shp", "Plots (delivered: meters, use, people and flow)")
    if pl:
        use_style(pl); add(g, pl, visible=False)
    me = vec("03_Plots_meters/Electricity_meters.shp", "Electricity meters (delivered)")
    if me:
        meters_style(me); add(g, me, visible=False)
    add(g, vec("03_Plots_meters/Plots_full_W14.shp", "Plots, full W14 layer (56 fields)", "Cadastral_plot"), visible=False)

    # ---- hydrology
    g = group("Hydrology", expanded=False)
    add(g, vec("04_Hydrology/Streams NSA 2m project boundary.shp", "Streams (NSA 2 m, project boundary)", "Streams_NSA_2m_project_boundary"))
    add(g, vec("04_Hydrology/Upstream Catchments.shp", "Upstream catchments", "Upstream_Catchments"), visible=False)
    for t in (10, 25, 50, 100, 500):
        add(g, ras(f"04_Hydrology/Hazard_T{t}y.tif", f"Flood hazard, T = {t} years", "Hazard_T50y"), visible=(t == 50))

    # ---- roads, population, terrain
    g = group("Roads"); add(g, vec("05_Roads/Road_Centercline.shp", "Road centrelines (dual carriageways flagged)", "Road_Centercline"))
    g = group("Population", expanded=False); add(g, ras("06_Population/GHS POP 2025 IBRI.tif", "GHS population 2025", "GHS_POP_2025_IBRI"), visible=False)
    g = group("Terrain", expanded=False)
    add(g, ras("07_Terrain/IBRI_terrain_2m.tif", "Terrain, 2 m (from the 0.5 m clip)", "IBRI_0p5_clip"), visible=False)
    hs = ras("07_Terrain/IBRI_terrain_2m_hillshade.tif", "Hillshade, 2 m")
    if hs:
        hs.setOpacity(0.6); add(g, hs, visible=False)

    # ---- existing network and the design
    g = group("Existing network", expanded=False)
    add(g, vec("08_Existing_network/Main Pipe.shp", "Main pipe", "Main_Pipe"))
    add(g, vec("08_Existing_network/Sub Main Pipe guide.shp", "Sub-main pipe guide", "Sub_Main_Pipe_guide"), visible=False)
    add(g, vec("08_Existing_network/IBRI STP.shp", "Ibri STP", "IBRI_STP"))
    gg = g.addGroup("NAMA wastewater assets (received)"); gg.setExpanded(False)
    for f, nm, st in (("SEWERLINE_IBRI", "Existing gravity sewer", "Existing_gravity_sewer"), ("FORCELINE_IBRI", "Existing force mains", "Existing_force_mains"),
                      ("TE_LINE_IBRI", "Existing treated effluent main", "Existing_treated_effluent_main"), ("GR_TEPS_IBRI", "Existing pumping station", "Existing_pumping_station"),
                      ("STP_PT_IBRI", "STP location", "STP_location"), ("STP_BUILDING_IBRI", "STP structures", "STP_structures")):
        add(gg, vec(f"08_Existing_network/NAMA_wastewater/{f}.shp", nm, st))
    g = group("PAEW (received)", expanded=False, checked=False)
    for sub, nm, st in (("PW_Mains", "PAEW water mains", "PAEW_water_mains"), ("PW_Laterals", "PAEW water laterals", "PAEW_water_laterals"),
                        ("PW_Services", "PAEW water services", "PAEW_water_services"), ("PW_System_Valves", "PAEW system valves", "PAEW_system_valves"),
                        ("PW_Hydrants", "PAEW hydrants", "PAEW_hydrants"), ("PW_Facilities", "PAEW facilities", "PAEW_facilities"),
                        ("PW_Facility_Boundaries", "PAEW facility boundaries", "PAEW_facility_boundaries")):
        add(g, vec("09_PAEW/PAEW_MAIN.kmz", nm, st, sub=sub), visible=sub in ("PW_Mains", "PW_Laterals", "PW_Services"))
    for f, nm, st in (("Al_Raybah_110", "Al Raybah 110 mm", "Al_Raybah_110_mm"), ("Al_Raybah_180", "Al Raybah 180 mm", "Al_Raybah_180_mm"), ("Al_Raybah_225", "Al Raybah 225 mm", "Al_Raybah_225_mm")):
        add(g, vec(f"09_PAEW/{f}.kmz", nm, st), visible=False)
    g = group("Network design W15", expanded=False, checked=False)
    add(g, vec("11_Network_design_W15/W13_A_tree_pipes.shp", "W15 pipes", "W15_pipes"))
    add(g, vec("11_Network_design_W15/W13_A_tree_outlets.shp", "W15 outlets", "W15_outlets"), visible=False)
    add(g, vec("11_Network_design_W15/W15_A_groups.shp", "W15 catchments by group", "W15_catchments_by_group"), visible=False)
    # the engineer's W15 KMZ stays in the folder for Google Earth: its hundreds of subnetwork
    # folders would be hundreds of layers here

    # ---- identified projects (data layers) and the basemap
    g = group("Identified projects", expanded=False)
    add(g, vec("10_Identified_projects/Identified_projects_footprints.shp", "Identified projects, footprints (delivered)", "Identified_site"), visible=False)
    gs = QgsRasterLayer(GOOGLE, "Google Satellite", "wms")
    if gs.isValid():
        gs.setOpacity(0.5); proj.addMapLayer(gs, False); root.addLayer(gs)
    else:
        print("   Google Satellite layer invalid")

    proj.write(PROJECT)
    print("wrote", PROJECT, "|", len(proj.mapLayers()), "layers")

    # ---- a rendered check of the report copies over the boundary
    def render(layers, name, w=1800):
        ms = QgsMapSettings(); ms.setLayers(layers); ms.setBackgroundColor(QColor("#FFFFFF"))
        ext = QgsRectangle(429568, 2554439, 480010, 2583936); ms.setExtent(ext); ms.setOutputSize(QSize(w, int(w * ext.height() / ext.width())))
        ms.setDestinationCrs(QgsCoordinateReferenceSystem("EPSG:32640")); ms.setFlag(Qgis.MapSettingsFlag.DrawLabeling, True)
        job = QgsMapRendererParallelJob(ms); job.start(); job.waitForFinished()
        out = os.path.join(M, "_styles", f"check_{name}.png"); job.renderedImage().save(out); print("   check ->", out)
    render([s_people, b_upd], "people")
    render([ar, s_over, b_upd], "overflow")
    render([pq, b_upd], "plot_flow")
    render([hs] if hs else [], "hillshade") if hs else None
    app.exitQgis()


if __name__ == "__main__":
    build()
