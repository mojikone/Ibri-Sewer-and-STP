"""Map of the drops over 2 m of one case by the fix that removes them (drops_engine.py), on the frame of the report maps.
Runs in the standalone QGIS python:  & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" drops_map.py SC1-2056
Writes <case>/map_drops_<case>.png and adds nothing to the design's QGIS project."""
import json, os, sys
sys.stdout.reconfigure(line_buffering=True)
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(W18, "gis"))
import final_maps as FM
from final_maps import M
from qgis.core import (QgsApplication, QgsProject, QgsRasterLayer, QgsCoordinateReferenceSystem, QgsRectangle, QgsCategorizedSymbolRenderer,
                       QgsRendererCategory, QgsMarkerSymbol, QgsLineSymbol, QgsSingleSymbolRenderer)

CASE = sys.argv[1] if len(sys.argv) > 1 else "SC1-2056"
FIX = [("F1 regrade", "#1a9850", "F1 regrade: the pipe follows the falling ground"),
       ("F2 lower the branch, 4 %", "#4575b4", "F2 the branch lowered, gradients to 4 %"),
       ("F2 lower the branch, steeper than 4 % (to 3 m/s)", "#fdae61", "F2 the branch lowered, gradients above 4 % (to 3 m/s)"),
       ("F4 reconnect (candidate)", "#984ea3", "F4 reconnected to a nearby manhole"),
       ("F3 parallel shallow sewer", "#00a3a3", "F3 parallel shallow sewer"),
       ("vortex drop shaft", "#d7191c", "Vortex drop shaft")]


def main():
    app = QgsApplication([], True); app.initQgis()
    proj = QgsProject.instance(); proj.clear(); proj.setCrs(QgsCoordinateReferenceSystem("EPSG:32640"))
    bnd = M.vec(FM.BND, "Project boundary"); M.style_boundary(bnd); proj.addMapLayer(bnd, False)
    stl = M.vec(FM.STL, "Settlement boundary"); M.style_settlements(stl); proj.addMapLayer(stl, False)
    google = QgsRasterLayer(M.GOOGLE, "Satellite image (Google)", "wms"); google.setOpacity(0.3); proj.addMapLayer(google, False)
    pipes = FM.lyr(os.path.join(FM.R, CASE, "products", "map.gpkg"), "pipes", "Sewers")
    pipes.setRenderer(QgsSingleSymbolRenderer(QgsLineSymbol.createSimple({"color": "#8c8c8c", "width": "0.18"}))); proj.addMapLayer(pipes, False)
    dr = FM.lyr(os.path.join(HERE, CASE, f"drops_{CASE}.gpkg"), "drops_over_2m", "Drops over 2 m")
    have = set(dr.uniqueValues(dr.fields().indexOf("recommended")))
    size = lambda f: "4.2" if f == "vortex drop shaft" else "3.2" if "3 m/s" in f or "F4" in f or "F3" in f else "2.2"
    dr.setRenderer(QgsCategorizedSymbolRenderer("recommended", [QgsRendererCategory(f, QgsMarkerSymbol.createSimple(
        {"name": "circle", "color": c, "outline_color": "#ffffff", "outline_width": "0.3", "size": size(f)}), lab) for f, c, lab in FIX if f in have]))
    proj.addMapLayer(dr, False)
    S = json.load(open(os.path.join(HERE, CASE, "summary.json")))
    short = {"F1 regrade": "F1 regrade", "F2 lower the branch, 4 %": "F2 lowered, to 4 %", "F2 lower the branch, steeper than 4 % (to 3 m/s)": "F2 lowered, above 4 %",
             "F4 reconnect (candidate)": "F4 reconnected", "F3 parallel shallow sewer": "F3 parallel sewer", "vortex drop shaft": "Vortex drop shaft"}
    rows = [("Drops over 2 m (manholes)", f"{S['drops_over_2m']:,} ({S['manholes']:,})")] + [(short[f], f"{S['recommended'].get(f, 0):,}") for f, c, lab in FIX if f in have]
    ext = QgsRectangle(bnd.extent()); ext.scale(1.04)
    FM.make_map(proj, google, "drops", f"{CASE.split('-')[0]} ({CASE.split('-')[1]}): drops over 2 m by the fix that removes them",
                [dr, pipes, stl, bnd], [(dr, False), (pipes, False), (bnd, False)], ext, rows,
                os.path.join(HERE, CASE, f"map_drops_{CASE}.png"), [dr, pipes])
    app.exitQgis()


if __name__ == "__main__":
    main()
