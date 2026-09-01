"""Map figures for the Concept Design Report.

Run this inside the QGIS Python console, or through the qgis MCP bridge. It
clones the project's existing A3 landscape layout for each figure so every map
carries the same frame, legend, scale bar and north arrow, then exports a PNG
into the report's img folder.
"""
import os

from qgis.core import (QgsLayoutExporter, QgsLayoutItemLabel, QgsLayoutItemMap,
                       QgsLayoutItemLegend, QgsProject, QgsRectangle,
                       QgsCoordinateTransform, QgsCoordinateReferenceSystem,
                       QgsLayoutItemPicture, QgsReadWriteContext)
from qgis.core import QgsLayoutSize, QgsLayoutPoint, QgsUnitTypes
from qgis.PyQt.QtGui import QColor
from qgis.PyQt.QtXml import QDomDocument

UNIT_MM = QgsUnitTypes.LayoutMillimeters

OUT = (r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude"
       r"\W9\report\img")
TEMPLATE = "W2 M1 Study Area"
SUBTITLE = "Ibri Sewer, TE Networks and STP — Concept Design Report | Renardet 2621"

# figure key: (layout title, [layer names, drawn bottom to top], basemap,
#              [(label, value) rows for the data box])
FIGURES = {
    "M01_location": (
        "Project location and study area boundary",
        ["Project Boundary updated", "Towns"], True,
        [("Study area", "531.4 km2"), ("Settlements", "25"),
         ("Wilayat", "Ibri, Adh Dhahirah"), ("Projection", "UTM 40N, WGS 84")]),
    "M02_wastewater": (
        "Wastewater assets: constructed and proposed",
        ["Project Boundary updated", "Existing gravity sewer",
         "Existing treated effluent main", "Existing force mains",
         "Existing pumping station", "STP location"], True,
        [("Gravity sewer, built 2006", "111.6 km"),
         ("Gravity sewer, proposed", "199.3 km"),
         ("Force main, built 2006", "10.0 km"),
         ("Pumping main, proposed", "23.2 km"),
         ("Treated effluent, proposed", "45.7 km"),
         ("Pumping stations", "1"),
         ("Treatment plant", "1,800 m3/d")]),
    "M03_water": (
        "Potable water network within the study area",
        ["Project Boundary updated", "PAEW water mains",
         "PAEW water laterals", "PAEW facilities"], True,
        [("Water mains", "647.8 km"), ("Laterals", "8.1 km"),
         ("System valves", "1,586"), ("Hydrants", "568"),
         ("Source", "PAEW dataset")]),
    "M04_electricity": (
        "Electricity accounts by consumption category",
        ["Project Boundary updated", "Electricity accounts by category"], True,
        [("Accounts", "33,970"), ("Domestic", "22,588"),
         ("Non-domestic", "9,392"), ("Governmental", "967"),
         ("Agricultural", "523")]),
    "M05_settlements": (
        "Settlements and cadastral plots",
        ["Project Boundary updated", "Towns", "MoH_Plots"], True,
        [("Settlements", "25"), ("Population 2024", "116,456"),
         ("Occupancy rate", "5.32 persons"), ("Source", "NCSI, MoHUP")]),
}


def _layers(names):
    proj = QgsProject.instance()
    found, missing = [], []
    for n in names:
        hit = [l for l in proj.mapLayers().values() if l.name() == n]
        if hit:
            found.append(hit[0])
        else:
            missing.append(n)
    if missing:
        print("   missing layers:", missing)
    return found


def _basemap():
    proj = QgsProject.instance()
    for n in ("Google Satellite", "ESRI Satellite", "Google satellite hydbrid"):
        hit = [l for l in proj.mapLayers().values() if l.name() == n]
        if hit:
            return hit[0]
    return None


def _clone(name):
    """Copy the template layout so every figure shares one frame."""
    proj = QgsProject.instance()
    mgr = proj.layoutManager()
    old = mgr.layoutByName(name)
    if old:
        mgr.removeLayout(old)
    src = mgr.layoutByName(TEMPLATE)
    doc = QDomDocument()
    el = src.writeXml(doc, QgsReadWriteContext())
    doc.appendChild(el)
    new = type(src)(proj)
    new.loadFromTemplate(doc, QgsReadWriteContext(), True)
    new.setName(name)
    mgr.addLayout(new)
    return new


def build(keys=None, dpi=200):
    os.makedirs(OUT, exist_ok=True)
    proj = QgsProject.instance()
    utm = QgsCoordinateReferenceSystem("EPSG:32640")

    bnd = [l for l in proj.mapLayers().values()
           if l.name() == "Project Boundary updated"][0]
    ext = bnd.extent()
    if bnd.crs() != utm:
        ext = QgsCoordinateTransform(bnd.crs(), utm,
                                     proj.transformContext()).transform(ext)
    ext = QgsRectangle(ext)
    ext.scale(1.06)

    made = []
    for key, (title, names, basemap, box) in FIGURES.items():
        if keys and key not in keys:
            continue
        print(key)
        lay = _clone("RPT " + key)
        legends = []

        stack = _layers(names)
        if basemap:
            bm = _basemap()
            if bm:
                stack = stack + [bm]

        for it in lay.items():
            if isinstance(it, QgsLayoutItemMap):
                it.setLayers(stack)
                it.setKeepLayerSet(True)
                it.zoomToExtent(ext)
            elif isinstance(it, QgsLayoutItemLegend):
                legends.append(it)
            elif isinstance(it, QgsLayoutItemLabel):
                t = it.text()
                if t.startswith("Ibri Sewer"):
                    it.setText(SUBTITLE)
                    it.attemptResize(QgsLayoutSize(200, 4.5, UNIT_MM))
                    it.attemptMove(QgsLayoutPoint(8, 9.6, UNIT_MM))
                elif t and not t.startswith("N"):
                    # the number belongs to the report caption alone; a map
                    # that numbers itself drifts as soon as a figure is added
                    it.setText(title)
                    it.attemptResize(QgsLayoutSize(200, 6.5, UNIT_MM))
                    it.attemptMove(QgsLayoutPoint(8, 2.8, UNIT_MM))

        # the legend must list only what the map draws, not the whole project
        mapitem = [i for i in lay.items() if isinstance(i, QgsLayoutItemMap)][0]
        for lg in legends:
            lg.setLinkedMap(mapitem)
            lg.setAutoUpdateModel(False)
            grp = lg.model().rootGroup()
            for ch in list(grp.children()):
                grp.removeChildNode(ch)
            for l in stack:
                if l.name() in ("Google Satellite", "ESRI Satellite",
                                "Google satellite hydbrid"):
                    continue
                node = grp.addLayer(l)
                # a categorised layer already names itself in each class
                # label, so the layer title above them would repeat it
                r = getattr(l, "renderer", lambda: None)()
                if r is not None and r.type() == "categorizedSymbol":
                    node.setCustomProperty("legend/title-style", "hidden")
            lg.setTitle("")
            lg.setResizeToContents(True)
            lg.adjustBoxSize()

        _fill_box(lay, box)

        path = os.path.join(OUT, key + ".png")
        exp = QgsLayoutExporter(lay)
        settings = QgsLayoutExporter.ImageExportSettings()
        settings.dpi = dpi
        res = exp.exportToImage(path, settings)
        made.append((key, res == QgsLayoutExporter.Success, path))
        print("   ", "ok" if res == QgsLayoutExporter.Success else "FAILED")

    proj.write()
    return made


if __name__ == "__console__":
    build()


# the template carries an empty white label behind the data table; the table
# is hinged to that label's lower-right corner and the label itself removed
BOX_ANCHOR = (286.3, 201.9)     # mm from the top-left of the page
BOX_WIDTH = 58.0                # mm
ROW_MM = 5.60                   # generous: the frame must not clip a row


def _fill_box(lay, rows):
    """Write the figure's data table and hinge it to the lower-right corner."""
    from qgis.core import (QgsLayoutFrame, QgsLayoutItemManualTable,
                           QgsLayoutItemLabel, QgsTableCell, QgsLayoutSize,
                           QgsLayoutPoint)

    # drop the empty backing label
    for it in list(lay.items()):
        if isinstance(it, QgsLayoutItemLabel) and not it.text().strip():
            lay.removeLayoutItem(it)

    for it in lay.items():
        if not isinstance(it, QgsLayoutFrame):
            continue
        mf = it.multiFrame()
        if not isinstance(mf, QgsLayoutItemManualTable):
            continue
        mf.setTableContents(
            [[QgsTableCell(str(k)), QgsTableCell(str(v))] for k, v in rows])
        mf.setIncludeTableHeader(False)
        mf.refresh()

        # height follows the row count: querying the multiframe for its own
        # size reports the frame rather than the table, which leaves a blank
        # strip under the last row
        w = BOX_WIDTH
        h = ROW_MM * len(rows)
        it.attemptResize(QgsLayoutSize(w, h, UNIT_MM))
        mf.recalculateFrameSizes()
        it.attemptMove(QgsLayoutPoint(BOX_ANCHOR[0] - w,
                                      BOX_ANCHOR[1] - h, UNIT_MM))
        # the frame is sized generously so no row is clipped; its background
        # is therefore switched off and the table paints its own, otherwise a
        # blank strip shows beneath the last row
        it.setBackgroundEnabled(False)
        it.setFrameEnabled(False)
        mf.setBackgroundColor(QColor(255, 255, 255, 235))
        return True
    return False
