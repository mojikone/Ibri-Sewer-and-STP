"""Copy the report's map layout ("W2 M1 Study Area" in stp2.qgz, the frame every R3 map was cloned from) into a
.qpt template that the W17 project can load. Read-only on stp2.qgz; runs in the standalone QGIS python:

    & "C:\\Program Files\\QGIS 3.44.8\\bin\\python-qgis-ltr.bat" extract_template.py
"""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from qgis.core import QgsApplication, QgsProject, QgsReadWriteContext, QgsLayoutItemLabel, QgsLayoutItemMap, QgsLayoutItemLegend, QgsLayoutFrame
from qgis.PyQt.QtXml import QDomDocument

HERE = os.path.dirname(os.path.abspath(__file__))
STP2 = os.path.join(HERE, "..", "..", "..", "QGIS", "QGIS 2621 ibri sewer stp2.qgz")
TEMPLATE = "W2 M1 Study Area"
OUT = os.path.join(HERE, "template_report_A3.qpt")

app = QgsApplication([], False); app.initQgis()
proj = QgsProject.instance()
ok = proj.read(os.path.abspath(STP2), QgsProject.ReadFlag.FlagDontResolveLayers | QgsProject.ReadFlag.FlagDontLoadLayouts * 0)
print("read stp2:", ok)
lay = proj.layoutManager().layoutByName(TEMPLATE)
print("layout found:", lay is not None, "| layouts in stp2:", len(proj.layoutManager().layouts()))
if lay:
    pc = lay.pageCollection()
    print("pages:", pc.pageCount(), "| page size mm:", pc.page(0).pageSize().width(), "x", pc.page(0).pageSize().height())
    for it in lay.items():
        if hasattr(it, "positionWithUnits") and not isinstance(it, type(pc.page(0))):
            p, s = it.positionWithUnits(), it.sizeWithUnits()
            extra = (" text=" + repr(it.text()[:60])) if isinstance(it, QgsLayoutItemLabel) else ""
            print(f"  {type(it).__name__:28s} at ({p.x():6.1f},{p.y():6.1f}) size ({s.width():6.1f},{s.height():6.1f}){extra}")
    ok = lay.saveAsTemplate(OUT, QgsReadWriteContext())
    print("template written:", ok, OUT)
app.exitQgis()
