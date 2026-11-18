"""W18 final design: the report map of the treated effluent network of Scenario SC4 (STP-2 and STP-5), on the frame of the
other report maps (final_maps.make_map): the mains by the plant that supplies them and their size, the customers by
supplying plant, the plants. Network: results/final_0.75pc_SC1-SC4/te/SC4_TE_network.gpkg (py/final_financial.py basis).
Runs in the standalone QGIS python:  & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" te_map_sc4.py
Writes report_final/img/map_SC4_TE_network.png."""
import json, os, sys
sys.stdout.reconfigure(line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import final_maps as FM
from final_maps import M
from qgis.core import (QgsApplication, QgsProject, QgsVectorLayer, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle,
                       QgsCategorizedSymbolRenderer, QgsRendererCategory, QgsLineSymbol, QgsMarkerSymbol, QgsProperty, QgsSymbolLayer)

G = os.path.join(FM.R, "te", "SC4_TE_network.gpkg")
FIN = json.load(open(os.path.join(FM.R, "financial.json")))["SC4"]
COL = {"STP-2": FM.PLANT_COLOUR["STP-2"], "STP-5": FM.PLANT_COLOUR["STP-5"]}


def main():
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); proj.clear(); proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    bnd = M.vec(FM.BND, "Project boundary"); M.style_boundary(bnd); proj.addMapLayer(bnd, False)
    stl = M.vec(FM.STL, "Settlement boundary"); M.style_settlements(stl); proj.addMapLayer(stl, False)
    google = QgsRasterLayer(M.GOOGLE, "Satellite image (Google)", "wms"); google.setOpacity(0.3); proj.addMapLayer(google, False)
    mains = FM.lyr(G, "te_mains", "Treated effluent mains")
    cats = []
    for p, c in COL.items():
        s = QgsLineSymbol.createSimple({"color": c, "width": "0.6", "capstyle": "round"})
        s.symbolLayer(0).setDataDefinedProperty(QgsSymbolLayer.PropertyStrokeWidth, QgsProperty.fromExpression('0.35 + "dn" / 400.0'))
        cats.append(QgsRendererCategory(p, s, f"Main supplied from {p} (width by size, 100 to 700 mm)"))
    mains.setRenderer(QgsCategorizedSymbolRenderer("source", cats)); proj.addMapLayer(mains, False)
    cu = FM.lyr(G, "customers", "Customers")
    cu.setRenderer(QgsCategorizedSymbolRenderer("sc4_source", [QgsRendererCategory(p, QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": c, "outline_color": "#ffffff", "outline_width": "0.3", "size": "2.4"}), f"Customer supplied from {p}") for p, c in COL.items()]))
    M.label(cu, '"id"', size=5.5, colour="#1a1a1a", bold=False, priority=5, dist=0.6); FM.scale_labels(cu); proj.addMapLayer(cu, False)
    pl = FM.lyr(G, "plants", "Treatment plants")
    pl.setRenderer(QgsCategorizedSymbolRenderer("stp", [QgsRendererCategory(p, QgsMarkerSymbol.createSimple(
        {"name": "square", "color": c, "outline_color": "#ffffff", "outline_width": "0.4", "size": "4.5"}), p) for p, c in COL.items()]))
    M.label(pl, '"stp"', size=7.0, colour="#1a1a1a", bold=True, priority=10, dist=1.0); FM.scale_labels(pl); proj.addMapLayer(pl, False)
    ext = QgsRectangle(bnd.extent()); ext.scale(1.04)
    s = FIN["supply"]
    rows = [("Treated effluent mains", f"{FIN['te']['km']:.1f} km"), ("Booster pumping, duty", f"{FIN['te']['kw']:,.0f} kW")]
    for p in ("STP-2", "STP-5"):
        rows.append((f"{p}: customers, demand 2070", f"{s[p]['customers']}, {s[p]['demand_2070']:,.0f} m³/d"))
        rows.append((f"{p}: delivered / demand, 2056", f"{s[p]['2056']['delivered']:,.0f} / {s[p]['2056']['demand']:,.0f} m³/d"))
    FM.make_map(proj, google, "SC4 TE", "SC4, STP-2 and STP-5: treated effluent network",
                [pl, cu, mains, stl, bnd], [(pl, False), (mains, False), (cu, False), (bnd, False)], ext, rows,
                os.path.join(FM.IMG, "map_SC4_TE_network.png"), [mains, cu, pl])
    app.exitQgis()


if __name__ == "__main__":
    main()
