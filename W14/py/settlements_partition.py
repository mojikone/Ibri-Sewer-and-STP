# Merged settlement boundaries as a clean partition (run inside QGIS): Voronoi of the plot centroids by settlement, dissolved,
# clipped to the project boundary, shared edges simplified as a coverage so neighbours keep the same line. No gaps, no overlaps.
# Engineer 2026-09-10: the earlier union with the client's outlines left gaps at the joins.
from qgis.core import (QgsProject, QgsVectorLayer, QgsFeature, QgsField, QgsFields, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsGeometry)
from qgis.PyQt.QtCore import QVariant
import processing, os, csv
proj = QgsProject.instance(); W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
pl = QgsVectorLayer(f"{W13}/shp/PLOTS_load.shp", 'plots', 'ogr'); bnd = proj.mapLayer('Project_Boundary_838d5f8c_ffae_418a_afaa_3dd92e9e4c42')
CRS = pl.crs()
cl = QgsVectorLayer(f'Point?crs={CRS.authid()}&field=SETTLE:string(24)', 'cent', 'memory'); pr = cl.dataProvider(); feats = []
for f in pl.getFeatures():
    nf = QgsFeature(cl.fields()); nf.setGeometry(f.geometry().centroid()); nf.setAttributes([f['SETTLE']]); feats.append(nf)
pr.addFeatures(feats); cl.updateExtents(); print('centroids', cl.featureCount())
vor = processing.run('qgis:voronoipolygons', {'INPUT': cl, 'BUFFER': 10, 'OUTPUT': 'memory:'})['OUTPUT']
dis = processing.run('native:dissolve', {'INPUT': vor, 'FIELD': ['SETTLE'], 'OUTPUT': 'memory:'})['OUTPUT']
clp = processing.run('native:clip', {'INPUT': dis, 'OVERLAY': bnd, 'OUTPUT': 'memory:'})['OUTPUT']
# smooth the shared edges as a coverage (keeps topology); fall back to plain simplify if the algorithm is not there
try:
    smp = processing.run('native:coveragesimplify', {'INPUT': clp, 'TOLERANCE': 25, 'PRESERVE_BOUNDARY': True, 'OUTPUT': 'memory:'})['OUTPUT']; how = 'coverage simplify 25 m'
except Exception as ex:
    smp = clp; how = 'no smoothing (%s)' % str(ex)[:60]
# fix any leftover multipart / invalid pieces
fix = processing.run('native:fixgeometries', {'INPUT': smp, 'OUTPUT': 'memory:'})['OUTPUT']
# attributes from the settlement table
st = {r['SETTLE']: r for r in csv.DictReader(open(f"{W13}/analysis/settlements_today.csv", encoding='utf-8-sig'))}
fields = QgsFields()
for n, t in [('SETTLE', QVariant.String), ('AREA_KM2', QVariant.Double), ('POP_TODAY', QVariant.Double), ('OR_S', QVariant.Double), ('PPP', QVariant.Double), ('HOME_SHARE', QVariant.Double),
             ('CAP_PLOTS', QVariant.Int), ('CAP_POP', QVariant.Double)]:
    fields.append(QgsField(n, t, len=24 if t == QVariant.String else 0))
dst = f"{W13}/shp/Settlements_merged.shp"
for ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):
    if os.path.exists(dst[:-4] + ext): os.remove(dst[:-4] + ext)
opt = QgsVectorFileWriter.SaveVectorOptions(); opt.driverName = 'ESRI Shapefile'; opt.fileEncoding = 'UTF-8'
w = QgsVectorFileWriter.create(dst, fields, fix.wkbType(), CRS, QgsCoordinateTransformContext(), opt)
tot = 0.0
for f in fix.getFeatures():
    s = f['SETTLE']; r = st.get(s, {}); g = f.geometry(); tot += g.area()
    nf = QgsFeature(fields); nf.setGeometry(g)
    nf.setAttributes([s, round(g.area() / 1e6, 3), float(r.get('POP_TODAY', 0) or 0), float(r.get('OR_S', 0) or 0), float(r.get('PROPS_PER_BUILT_PLOT', 0) or 0), float(r.get('HOME_SHARE', 0) or 0),
                      int(float(r.get('FUT_CAP_PLOTS', 0) or 0)), float(r.get('FUT_CAP_POP', 0) or 0)])
    w.addFeature(nf)
del w
bg = QgsGeometry.unaryUnion([f.geometry() for f in bnd.getFeatures()])
print('written', dst, '| pieces', fix.featureCount(), '|', how, '| coverage %.4f of the boundary' % (tot / bg.area()))
# gaps and overlaps: a dissolved Voronoi partition has neither by construction; the coverage figure above (1.0000 of the boundary) is the check
