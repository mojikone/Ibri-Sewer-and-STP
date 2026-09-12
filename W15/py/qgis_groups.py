"""qgis_groups — build the QGIS groups of a W15 run by the major groups of run/groups.json
(engineer, 2026-09-12: the QGIS groups follow how the subnetworks converge, not the towns).

Run INSIDE QGIS (the qgis MCP execute_code, or the Python console):

    exec(open(r"D:/.../W15/py/qgis_groups.py", encoding="utf-8").read())

It removes the old "Claude W15" group, then builds one subgroup per major group, each with
the pipes (styled by qgis/W15_pipes.qml, filtered to the group's subnetworks), the outlets
and the catchments of that group, plus a whole-area layer set on top. Every symbol edit is
done through style files or fresh layers, never by chaining getters (the PyQGIS crash of
2026-09-12).
"""
import json
import os

from qgis.core import (QgsProject, QgsVectorLayer, QgsLayerTreeGroup, QgsFillSymbol, QgsMarkerSymbol,
                       QgsSingleSymbolRenderer, QgsCategorizedSymbolRenderer, QgsRendererCategory,
                       QgsPalLayerSettings, QgsTextFormat, QgsVectorLayerSimpleLabeling, Qgis)

W15 = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W15"
GROUP_NAME = "Claude W15"
proj = QgsProject.instance()
root = proj.layerTreeRoot()
old = root.findGroup(GROUP_NAME)
if old is not None:
    def _strip(grp):
        for ch in list(grp.children()):
            if hasattr(ch, "layerId"):
                proj.removeMapLayer(ch.layerId())
            elif hasattr(ch, "children"):
                _strip(ch)
    _strip(old)
    root.removeChildNode(old)
top = QgsLayerTreeGroup(GROUP_NAME)
root.insertChildNode(0, top)
groups = json.load(open(os.path.join(W15, "run", "groups.json"), encoding="utf-8"))
qml = os.path.join(W15, "qgis", "W15_pipes.qml")
shp = os.path.join(W15, "shp")
made = []


def _label(lyr, expr, size=8, scale=50000):
    pal = QgsPalLayerSettings(); pal.fieldName = expr; pal.isExpression = True
    pal.placement = Qgis.LabelPlacement.OverPoint
    pal.scaleVisibility = True; pal.minimumScale = float(scale); pal.maximumScale = 0.0
    tf = QgsTextFormat(); tf.setSize(size); pal.setFormat(tf)
    lyr.setLabeling(QgsVectorLayerSimpleLabeling(pal)); lyr.setLabelsEnabled(True)


def _subset(ids):
    return "\"CATCH\" IN (" + ",".join("'%s'" % i for i in ids) + ")"


# the whole-area layers, unticked
whole = QgsLayerTreeGroup("whole network"); top.addChildNode(whole)
for name, fn, style in (("W15 catchments by group", "W15_A_groups.shp", "groups"),
                        ("W15 outlets", "W13_A_tree_outlets.shp", "outlets"),
                        ("W15 pipes", "W13_A_tree_pipes.shp", "pipes")):
    lyr = QgsVectorLayer(os.path.join(shp, fn), name, "ogr")
    if not lyr.isValid():
        continue
    if style == "pipes":
        lyr.loadNamedStyle(qml)
    elif style == "groups":
        cats = []
        palette = ["#a6cee3", "#b2df8a", "#fdbf6f", "#cab2d6", "#fb9a99", "#ffff99", "#1f78b4", "#33a02c", "#ff7f00", "#6a3d9a"]
        for k, g in enumerate(groups["groups"]):
            sym = QgsFillSymbol.createSimple({"color": palette[k % len(palette)] + "66", "outline_color": "#555555", "outline_width": "0.3"})
            cats.append(QgsRendererCategory(g, sym, g))
            sym2 = QgsFillSymbol.createSimple({"color": palette[k % len(palette)] + "33", "outline_color": "#999999", "outline_width": "0.2", "outline_style": "dash"})
            cats.append(QgsRendererCategory(g + " (pocket)", sym2, g + " (pocket)"))
        lyr.setRenderer(QgsCategorizedSymbolRenderer("GROUP", cats))
    else:
        lyr.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "diamond", "color": "#e31a1c", "outline_color": "#000000", "outline_width": "0.3", "size": "3", "size_unit": "MM"})))
        _label(lyr, "\"CATCH\" || ' ' || \"OUT_TYPE\" || ' ' || round(\"KM\", 1) || ' km'", 8, 100000)
    proj.addMapLayer(lyr, False); n = whole.addLayer(lyr); n.setItemVisibilityChecked(style == "groups"); made.append(name)
whole.setItemVisibilityChecked(True)

# one subgroup per major group, pipes styled, filtered to its subnetworks
for gname, info in groups["groups"].items():
    ids = info["ids"]
    sub = QgsLayerTreeGroup(f"{gname}: {info['subnetworks']} subnetworks, {info['km']} km"); top.addChildNode(sub)
    for name, fn, style in (("pipes", "W13_A_tree_pipes.shp", "pipes"), ("outlets", "W13_A_tree_outlets.shp", "outlets"),
                            ("catchments", "W13_A_tree_catchments.shp", "catch")):
        lyr = QgsVectorLayer(os.path.join(shp, fn), f"{name} - {gname}", "ogr")
        if not lyr.isValid():
            continue
        lyr.setSubsetString(_subset(ids))
        if style == "pipes":
            lyr.loadNamedStyle(qml)
        elif style == "outlets":
            lyr.setRenderer(QgsSingleSymbolRenderer(QgsMarkerSymbol.createSimple({"name": "diamond", "color": "#e31a1c", "outline_color": "#000000", "outline_width": "0.3", "size": "3", "size_unit": "MM"})))
            _label(lyr, "\"CATCH\" || ' ' || \"OUT_TYPE\" || ' ' || round(\"KM\", 1) || ' km'", 8, 100000)
        else:
            lyr.setRenderer(QgsSingleSymbolRenderer(QgsFillSymbol.createSimple({"color": "#ffffff00", "outline_color": "#555555", "outline_width": "0.35"})))
        proj.addMapLayer(lyr, False); n = sub.addLayer(lyr); n.setItemVisibilityChecked(style == "pipes"); made.append(lyr.name())
    sub.setItemVisibilityChecked(False)
top.setItemVisibilityChecked(True)
print(len(made), "layers in", GROUP_NAME)
