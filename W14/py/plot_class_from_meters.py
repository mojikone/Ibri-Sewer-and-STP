# Derive each plot's main land use from the electricity meters on it (run inside QGIS).
from qgis.core import (QgsProject, QgsSpatialIndex, QgsCoordinateTransform, QgsVectorLayer, QgsField, QgsFields,
                       QgsFeature, QgsVectorFileWriter, QgsCoordinateTransformContext, QgsWkbTypes, QgsGeometry)
from qgis.PyQt.QtCore import QVariant
from collections import Counter, defaultdict
import csv, os

proj = QgsProject.instance()
plots = proj.mapLayer('PLOTS_59e7ed1e_b22c_49e9_a772_f89c0f58fca6')
ele = proj.mapLayer('shifted_Electric__Points_84b1d5d1_800f_480a_baba_5855fd020f64')
crt = [l for l in proj.mapLayers().values() if l.name() == 'CRT accounts identified (W13)'][0]
sites = [l for l in proj.mapLayers().values() if l.name() == 'Identified projects, OSM footprints (W13)'][0]
OUT = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"

tr_e = QgsCoordinateTransform(ele.crs(), plots.crs(), proj)
tr_c = QgsCoordinateTransform(crt.crs(), plots.crs(), proj)
idx = QgsSpatialIndex(plots.getFeatures())
pf = {f.id(): f for f in plots.getFeatures()}

GROUP = {'Primary Account Tariff': 'dom', 'Primary Account Tariff (with National Subsidy)': 'dom', 'Additional Account Tariff': 'dom_add',
         'Commercial': 'com', 'Fisheries': 'com', 'Tourism': 'com', 'Government': 'gov', 'MOD': 'gov', 'Agricultural': 'agr',
         'CRT Seasonal': 'crt', 'CRT Time of Use': 'crt', 'CRT Fixed Rate': 'crt', 'Industrial': 'ind'}

def plot_of(pt):
    for i in idx.intersects(QgsGeometry.fromPointXY(pt).boundingBox()):
        if pf[i].geometry().contains(pt):
            return i
    return None

acc = defaultdict(Counter); unplaced = Counter()
for f in ele.getFeatures():
    pt = tr_e.transform(f.geometry().asPoint()); i = plot_of(pt); g = GROUP.get(f['Name'], 'other')
    if i is None: unplaced[g] += 1
    else: acc[i][g] += 1
crt_use = defaultdict(Counter)
for f in crt.getFeatures():
    i = plot_of(tr_c.transform(f.geometry().asPoint()))
    if i is not None: crt_use[i][f['USE']] += 1
print('accounts placed on plots:', sum(sum(c.values()) for c in acc.values()), 'unplaced:', dict(unplaced))

# the two estates: industrial by footprint, workforce spread by plot area
estate = {}
WORKERS = {'صناعية الطيب': 4500, 'صناعية تنعم': 1800}
for s in sites.getFeatures():
    if s['name'] in WORKERS:
        g = s.geometry(); members = [i for i in idx.intersects(g.boundingBox()) if g.contains(pf[i].geometry().centroid())]
        ind = [i for i in members if pf[i]['Classes'] == 'Industrial']
        tot = sum(pf[i].geometry().area() for i in ind)
        for i in members: estate[i] = (s['name'], WORKERS[s['name']] * pf[i].geometry().area() / tot if i in ind else 0.0)
        print(s['name'], 'plots', len(members), 'industrial', len(ind), 'workers', WORKERS[s['name']])

def derive(i):
    c = acc.get(i, Counter()); n = sum(c.values())
    dom = c['dom'] + c['dom_add']; com = c['com']; gov = c['gov']; agr = c['agr']; u = crt_use.get(i, Counter())
    if i in estate: return 'Industrial', 'inside the estate footprint'
    if n == 0: return 'Unmetered', 'no meter on the plot'
    if u:
        top = u.most_common(1)[0][0]
        if top in ('Government', 'Education', 'Health', 'Religious'): return 'Government', f'CRT identified as {top}'
        if top == 'Industrial': return 'Industrial', 'CRT identified as Industrial'
        if top == 'Agricultural' and dom == 0: return 'Agricultural', 'CRT identified as Agricultural'
        if top == 'Commercial': return ('Commercial' if dom == 0 else 'Residential-Commercial'), f'CRT identified as Commercial, {dom} dwellings'
    if gov > 0 and gov >= com and gov >= dom: return 'Government', f'{gov} government meters'
    if com > 0 and dom == 0: return 'Commercial', f'{com} shop meters, no dwelling'
    if com > 0 and dom > 0: return 'Residential-Commercial', f'{com} shop + {dom} dwelling meters'
    if agr > 0 and dom == 0 and com == 0: return 'Agricultural', f'{agr} farm meters only'
    if agr > 0 and dom > 0: return 'Residential', f'{dom} dwellings on a farm plot ({agr} pump meters)'
    if dom > 0: return 'Residential', f'{dom} dwelling meters'
    if c['crt'] > 0: return 'Unresolved', 'CRT only, use unknown'
    return 'Unresolved', str(dict(c))

fields = QgsFields()
for fn in plots.fields(): fields.append(fn)
for name, t in [('N_ACC', QVariant.Int), ('N_DOM', QVariant.Int), ('N_DOMADD', QVariant.Int), ('N_COM', QVariant.Int), ('N_GOV', QVariant.Int),
                ('N_AGR', QVariant.Int), ('N_CRT', QVariant.Int), ('N_IND', QVariant.Int), ('DERIVED', QVariant.String), ('WHY', QVariant.String),
                ('AGREE', QVariant.String), ('ESTATE', QVariant.String), ('WORKERS', QVariant.Double)]:
    fields.append(QgsField(name, t, len=80 if t == QVariant.String else 0))
dst = f"{OUT}/shp/PLOTS_derived_class.shp"
opt = QgsVectorFileWriter.SaveVectorOptions(); opt.driverName = 'ESRI Shapefile'; opt.fileEncoding = 'UTF-8'
w = QgsVectorFileWriter.create(dst, fields, plots.wkbType(), plots.crs(), QgsCoordinateTransformContext(), opt)
conf = Counter(); rows = []
for i, f in pf.items():
    c = acc.get(i, Counter()); d, why = derive(i)
    moh = f['Classes']
    if d == 'Unmetered': agree = 'unmetered'
    elif d == moh: agree = 'same'
    elif d == 'Government' or moh == 'Proposed': agree = 'new'
    else: agree = 'differs'
    conf[(moh, d)] += 1
    nf = QgsFeature(fields); nf.setGeometry(f.geometry())
    vals = list(f.attributes()) + [sum(c.values()), c['dom'], c['dom_add'], c['com'], c['gov'], c['agr'], c['crt'], c['ind'], d, why, agree,
                                   estate[i][0] if i in estate else '', round(estate[i][1], 1) if i in estate else 0.0]
    nf.setAttributes(vals); w.addFeature(nf)
del w
print('written', dst)
with open(f"{OUT}/analysis/plot_class_confusion.csv", 'w', newline='', encoding='utf-8-sig') as fh:
    cw = csv.writer(fh); cw.writerow(['MoH_Classes', 'DERIVED', 'plots'])
    for (m, d), n in sorted(conf.items(), key=lambda x: -x[1]): cw.writerow([m, d, n])
tot_m = Counter(); tot_d = Counter()
for (m, d), n in conf.items(): tot_m[m] += n; tot_d[d] += n
print('MoH classes:', dict(tot_m.most_common()))
print('DERIVED:', dict(tot_d.most_common()))
print('confusion (MoH -> derived), top 25:')
for (m, d), n in sorted(conf.items(), key=lambda x: -x[1])[:25]: print(f'  {m:24s} -> {d:24s} {n}')
