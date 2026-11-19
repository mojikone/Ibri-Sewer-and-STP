"""The two maps the team placed in Chapter 6, redrawn on the network of the final design (engineer, 2026-11-19: "Figure
6-2 shows the STP options on old subnetworks"): the proposed treatment sites, and the existing and potential TE
customers. Sites from the team's layer (W: 10_TSE/SHP/Revised_STPs.shp), customers from their TE register
(results/final_0.75pc_SC1-SC4/te/te_customers.csv); the land each plant needs at its 2056 design capacity
(py/final_financial.py), the largest over the scenarios, in the data box (a footprint is too small to show at this scale).
Runs in the standalone QGIS python:  & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" team_maps_redraw.py
Writes report_final/img/map_stp_sites.png and map_te_customers.png."""
import json, math, os, sys
sys.stdout.reconfigure(line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import final_maps as FM
from final_maps import M
import pandas as pd
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle, QgsFeature,
                       QgsGeometry, QgsPointXY, QgsField, QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsMarkerSymbol, QgsFillSymbol,
                       QgsLineSymbol, QgsSingleSymbolRenderer, QgsProperty, QgsSymbolLayer)
from qgis.PyQt.QtCore import QVariant

SITES = r"W:\2621 Design and Supervision for STP, Sewer & TE Networks System in Ibri_NAMA\06-WORKING\04-Hydraulic\10_TSE\SHP\Revised_STPs.shp"
FIN = json.load(open(os.path.join(FM.R, "financial.json")))
USED = {"STP-1": ["SC1", "SC3"], "STP-2": ["SC2", "SC4"], "STP-5": ["SC3", "SC4"]}


def mem(kind, name, fields):
    l = QgsVectorLayer(f"{kind}?crs=EPSG:32640", name, "memory"); l.dataProvider().addAttributes([QgsField(n, t) for n, t in fields]); l.updateFields(); return l


def main():
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); proj.clear(); proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    bnd = M.vec(FM.BND, "Project boundary"); M.style_boundary(bnd); proj.addMapLayer(bnd, False)
    stl = M.vec(FM.STL, "Settlement boundary"); M.style_settlements(stl); proj.addMapLayer(stl, False)
    google = QgsRasterLayer(M.GOOGLE, "Satellite image (Google)", "wms"); google.setOpacity(0.3); proj.addMapLayer(google, False)
    net = FM.lyr(os.path.join(FM.R, "SC1-2056", "products", "map.gpkg"), "pipes", "Sewer network (final design)")
    net.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#7f8a99", "width": "0.2"}))); proj.addMapLayer(net, False)
    src = QgsVectorLayer(SITES, "sites", "ogr")
    pts = mem("Point", "Treatment sites", [("site", QVariant.String), ("state", QVariant.String), ("label", QVariant.String)])
    rings = mem("Polygon", "Plant footprint, 2056 design capacity", [("site", QVariant.String)])
    rows = []
    for f in src.getFeatures():
        site = f["Name"].split(":")[0].strip(); p = f.geometry().asPoint()
        used = site in USED
        if used:
            land = max(FIN[sc]["plants"][site]["total"] * FIN[sc]["plants"][site]["land_per"] for sc in USED[site])
            cap = max(FIN[sc]["plants"][site]["total"] for sc in USED[site])
            g = QgsGeometry.fromPointXY(QgsPointXY(p)).buffer(math.sqrt(land / math.pi), 48)
            rf = QgsFeature(rings.fields()); rf.setGeometry(g); rf["site"] = site; rings.dataProvider().addFeature(rf)
            lab = f"{site} ({', '.join(USED[site])})"; rows.append((lab, f"{cap:,} m³/d, {land / 10000:.1f} ha"))
        else:
            lab = f"{site} (not used)"
        pf = QgsFeature(pts.fields()); pf.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(p)))
        pf["site"], pf["state"], pf["label"] = site, site if used else "not used", lab; pts.dataProvider().addFeature(pf)
    pts.updateExtents(); rings.updateExtents()
    pts.setRenderer(QgsCategorizedSymbolRenderer("state", [QgsRendererCategory(s, QgsMarkerSymbol.createSimple({"name": "square", "color": FM.PLANT_COLOUR[s],
        "outline_color": "#ffffff", "outline_width": "0.4", "size": "4.6"}), f"{s}, used in {' and '.join(USED[s])}") for s in USED] +
        [QgsRendererCategory("not used", QgsMarkerSymbol.createSimple({"name": "square", "color": "#9aa3ad", "outline_color": "#ffffff", "size": "3.6"}), "Candidate site not used by the scenarios")]))
    M.label(pts, '"label"', size=7.0, colour="#1a1a1a", bold=True, priority=10, dist=1.2); FM.scale_labels(pts)
    rings.setRenderer(QgsCategorizedSymbolRenderer("site", [QgsRendererCategory(s, QgsFillSymbol.createSimple({"color": FM.PLANT_COLOUR[s] + "55",
        "outline_color": FM.PLANT_COLOUR[s], "outline_width": "0.5"}), f"{s} land at the 2056 design capacity") for s in USED]))
    for l in (pts, rings): proj.addMapLayer(l, False)
    ext = QgsRectangle(bnd.extent()); ext.scale(1.04)
    FM.make_map(proj, google, "STP sites", "Proposed treatment sites and the sewer network of the final design",
                [pts, net, stl, bnd], [(pts, False), (net, False), (bnd, False)], ext,
                [("Site (scenarios)", "Design capacity 2056, land")] + rows, os.path.join(FM.IMG, "map_stp_sites.png"), [pts, net])
    # ---- TE customers
    C = pd.read_csv(os.path.join(FM.R, "te", "te_customers.csv")); C = C[C.x.notna()]
    cu = mem("Point", "TE customers", [("id", QVariant.String), ("d2070", QVariant.Double), ("kind", QVariant.String)])
    for r in C.itertuples():
        f = QgsFeature(cu.fields()); f.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(r.x, r.y))); f["id"] = r.id; f["d2070"] = float(r.d2070)
        f["kind"] = "Farmland and municipal" if r.d2070 >= 1000 else "Sports grounds, clubs and others"; cu.dataProvider().addFeature(f)
    cu.updateExtents()
    sym = lambda c: QgsMarkerSymbol.createSimple({"name": "circle", "color": c, "outline_color": "#ffffff", "outline_width": "0.3", "size": "2.6"})
    big = sym("#7B4FB0"); big.setDataDefinedSize(QgsProperty.fromExpression('2.6 + 0.0009 * "d2070"'))
    cu.setRenderer(QgsCategorizedSymbolRenderer("kind", [QgsRendererCategory("Farmland and municipal", big, "Farmland and municipal (size by 2070 demand)"),
                                                          QgsRendererCategory("Sports grounds, clubs and others", sym("#2E8B57"), "Sports grounds, clubs and others")]))
    M.label(cu, '"id"', size=6.0, colour="#1a1a1a", bold=False, priority=6, dist=0.8); FM.scale_labels(cu); proj.addMapLayer(cu, False)
    used_pts = mem("Point", "Treatment sites used by the scenarios", [("site", QVariant.String)])
    for f in pts.getFeatures():
        if f["state"] != "not used":
            g = QgsFeature(used_pts.fields()); g.setGeometry(f.geometry()); g["site"] = f["site"]; used_pts.dataProvider().addFeature(g)
    used_pts.setRenderer(QgsCategorizedSymbolRenderer("site", [QgsRendererCategory(s, QgsMarkerSymbol.createSimple({"name": "square", "color": FM.PLANT_COLOUR[s],
        "outline_color": "#ffffff", "size": "4.4"}), s) for s in USED]))
    M.label(used_pts, '"site"', size=7.0, colour="#1a1a1a", bold=True, priority=10, dist=1.2); FM.scale_labels(used_pts); proj.addMapLayer(used_pts, False)
    dem = lambda y: (C.d2030 + (C.d2070 - C.d2030) * (y - 2030) / 40).sum()
    FM.make_map(proj, google, "TE customers", "Existing and potential treated effluent customers",
                [used_pts, cu, net, stl, bnd], [(used_pts, False), (cu, False), (net, False), (bnd, False)], ext,
                [("Customers (with a location)", f"{len(C)} (31 registered)"), ("Demand 2031", f"{dem(2031) + 1205:,.0f} m³/d"),
                 ("Demand 2056", f"{dem(2056) + 1205 + (2200 - 1205) * 26 / 40:,.0f} m³/d"), ("Demand 2070", "26,705 m³/d")],
                os.path.join(FM.IMG, "map_te_customers.png"), [cu, used_pts])
    app.exitQgis()


if __name__ == "__main__":
    main()
