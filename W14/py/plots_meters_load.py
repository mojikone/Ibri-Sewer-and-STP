# W13 — meters onto plots, settlements, today's load per plot (steps 1-4 of 2026-09-09). Run inside QGIS.
#
# Rules (engineer, 2026-09-09):
#   every dwelling meter (primary, subsidised, additional) is one property at OR 5.32
#   164 L/c/d domestic; non-domestic 0.22 x 164 and governmental 0.14 x 164 PER PERSON, never compounded
#   special = the two estates' workforce (4,500 Al Tayyeb, 1,800 Tanam) spread by industrial plot area, 93 L/d each
#   sewage 85 % of domestic water, 54 % of the rest; farm meters carry no load
#   off-plot meters snap to the nearest plot within 15 m, else stay free
#   every plot belongs to the settlement it lies in, else the nearest; the two AL AYNAYN outlines are one
from qgis.core import (QgsProject, QgsSpatialIndex, QgsCoordinateTransform, QgsVectorLayer, QgsField, QgsFields, QgsFeature,
                       QgsVectorFileWriter, QgsCoordinateTransformContext, QgsGeometry, QgsPointXY, QgsFeatureRequest)
from qgis.PyQt.QtCore import QVariant
from collections import Counter, defaultdict
import csv, os, math, processing

proj = QgsProject.instance()
W13 = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W14"
plots = proj.mapLayer('PLOTS_59e7ed1e_b22c_49e9_a772_f89c0f58fca6')
ele = proj.mapLayer('shifted_Electric__Points_84b1d5d1_800f_480a_baba_5855fd020f64')
crt = [l for l in proj.mapLayers().values() if l.name() == 'CRT accounts identified (W13)'][0]
sites = [l for l in proj.mapLayers().values() if l.name() == 'Identified projects, OSM footprints (W13)'][0]
towns = proj.mapLayer('Towns_Boundary_selection_db139dbd_e41c_476f_b8c0_37bf23d1685e')
bnd = proj.mapLayer('Project_Boundary_838d5f8c_ffae_418a_afaa_3dd92e9e4c42')
CRS = plots.crs()

OR, LPCD, R_ND, R_GOV, L_IND, RET_DOM, RET_ND = 5.32, 164.0, 0.22, 0.14, 93.0, 0.85, 0.54
SNAP_M, BIG_M2 = 15.0, 2000.0
WORKERS = {'صناعية الطيب': ('AL TAYYEB', 4500.0), 'صناعية تنعم': ('TANAM', 1800.0)}
GROUP = {'Primary Account Tariff': 'dom', 'Primary Account Tariff (with National Subsidy)': 'dom', 'Additional Account Tariff': 'dom_add',
         'Commercial': 'com', 'Fisheries': 'com', 'Tourism': 'com', 'Government': 'gov', 'MOD': 'gov', 'Agricultural': 'agr',
         'CRT Seasonal': 'crt', 'CRT Time of Use': 'crt', 'CRT Fixed Rate': 'crt', 'Industrial': 'ind'}
GUD_OF_USE = {'Commercial': 'non_domestic', 'Telecom/Utility': 'non_domestic', 'Government': 'government', 'Education': 'government',
              'Health': 'government', 'Religious': 'government', 'Industrial': 'special', 'Agricultural': 'agricultural', 'Unresolved': 'non_domestic'}

def writer(path, fields, wkb, crs):
    for ext in ('.shp', '.shx', '.dbf', '.prj', '.cpg'):                     # OGR will not overwrite an existing shapefile
        if os.path.exists(path[:-4] + ext): os.remove(path[:-4] + ext)
    opt = QgsVectorFileWriter.SaveVectorOptions(); opt.driverName = 'ESRI Shapefile'; opt.fileEncoding = 'UTF-8'
    return QgsVectorFileWriter.create(path, fields, wkb, crs, QgsCoordinateTransformContext(), opt)

# ---------- plots, settlements ----------
pf = {f.id(): f for f in plots.getFeatures()}
pidx = QgsSpatialIndex(plots.getFeatures(), flags=QgsSpatialIndex.FlagStoreFeatureGeometries)
tr_t = QgsCoordinateTransform(towns.crs(), CRS, proj)
cores = defaultdict(list)
for f in towns.getFeatures():
    g = QgsGeometry(f.geometry()); g.transform(tr_t); cores[str(f['Name']).strip()].append(g)
core = {n: QgsGeometry.unaryUnion(gs) for n, gs in cores.items()}
names = sorted(core)
print('settlements:', len(names))
settle = {}; how = Counter()
for i, f in pf.items():
    c = f.geometry().centroid()
    hit = [n for n in names if core[n].contains(c)]
    if hit: settle[i] = hit[0]; how['inside'] += 1
    else:
        settle[i] = min(names, key=lambda n: core[n].distance(c)); how['nearest'] += 1
print('plot -> settlement:', dict(how))

# ---------- meters onto plots ----------
tr_e = QgsCoordinateTransform(ele.crs(), CRS, proj); tr_c = QgsCoordinateTransform(crt.crs(), CRS, proj)
crt_use = {}
for f in crt.getFeatures():
    crt_use[(round(f['lon'], 6), round(f['lat'], 6))] = f['USE']
mfields = QgsFields()
for name, t, ln in [('TARIFF', QVariant.String, 48), ('GROUP', QVariant.String, 8), ('GUD', QVariant.String, 14), ('USE', QVariant.String, 16), ('PLOT_FID', QVariant.Int, 0),
                    ('PLACE', QVariant.String, 8), ('SNAP_M', QVariant.Double, 0), ('SETTLE', QVariant.String, 24), ('PROPERTY', QVariant.Int, 0)]:
    mfields.append(QgsField(name, t, len=ln))
mpath = f"{W13}/shp/ELE_meters_on_plots.shp"
from qgis.core import QgsWkbTypes
mw = writer(mpath, mfields, QgsWkbTypes.Point, CRS)
acc = defaultdict(Counter); acc_gud = defaultdict(Counter); place = Counter(); free_settle = Counter()
for f in ele.getFeatures():
    p0 = f.geometry().asPoint(); pt = tr_e.transform(p0); g = GROUP.get(f['Name'], 'other')
    use = crt_use.get((round(p0.x(), 6), round(p0.y(), 6)), '') if g == 'crt' else ''
    gud = {'dom': 'domestic', 'dom_add': 'domestic', 'com': 'non_domestic', 'gov': 'government', 'agr': 'agricultural', 'ind': 'special'}.get(g)
    if g == 'crt': gud = GUD_OF_USE.get(use, 'non_domestic')
    gpt = QgsGeometry.fromPointXY(pt); fid = None; d = 0.0; pl = 'free'
    for i in pidx.intersects(gpt.boundingBox()):
        if pf[i].geometry().contains(pt): fid = i; pl = 'inside'; break
    if fid is None:
        best = None
        for i in pidx.nearestNeighbor(pt, 5, SNAP_M):
            dd = pf[i].geometry().distance(gpt)
            if dd <= SNAP_M and (best is None or dd < best[1]): best = (i, dd)
        if best: fid, d, pl = best[0], best[1], 'snapped'
    place[pl] += 1
    st = settle[fid] if fid is not None else min(names, key=lambda n: core[n].distance(gpt))
    if fid is not None: acc[fid][g] += 1; acc_gud[fid][gud] += 1
    else: free_settle[st] += 1
    nf = QgsFeature(mfields); nf.setGeometry(QgsGeometry.fromPointXY(pt))
    nf.setAttributes([f['Name'], g, gud, use, fid if fid is not None else -1, pl, round(d, 1), st, 1 if gud == 'domestic' else 0])
    mw.addFeature(nf)
del mw
print('meters placed:', dict(place), '| free meters by settlement:', dict(free_settle.most_common(5)))

# ---------- estates, workforce ----------
estate = {}
for s in sites.getFeatures():
    if s['name'] in WORKERS:
        g = s.geometry(); code, wf = WORKERS[s['name']]
        members = [i for i in pidx.intersects(g.boundingBox()) if g.contains(pf[i].geometry().centroid())]
        ind = [i for i in members if pf[i]['Classes'] == 'Industrial']; tot = sum(pf[i].geometry().area() for i in ind)
        for i in members: estate[i] = (code, wf * pf[i].geometry().area() / tot if i in ind else 0.0)

# ---------- today's load per plot ----------
def derived(i, c, u):
    dom = c['dom'] + c['dom_add']; com = c['com']; gov = c['gov']; agr = c['agr']
    if i in estate: return 'Industrial', 'EST'
    if sum(c.values()) == 0: return 'Unmetered', 'UNM'
    if u.get('government', 0) > 0 and u['government'] >= u.get('non_domestic', 0) and gov + u['government'] >= dom: return 'Government', 'GOV'
    if u.get('special', 0) > 0: return 'Industrial', 'IND'
    if gov > 0 and gov >= com and gov >= dom: return 'Government', 'GOV'
    if (com > 0 or u.get('non_domestic', 0) > 0) and dom == 0: return 'Commercial', 'COM'
    if (com > 0 or u.get('non_domestic', 0) > 0) and dom > 0: return 'Residential-Commercial', 'RC'
    if agr > 0 and dom == 0 and com == 0: return 'Agricultural', 'AGR'
    if agr > 0 and dom > 0: return 'Residential', 'RAG'
    if dom > 0: return 'Residential', 'RES'
    return 'Unresolved', 'UNR'

# settlement pools for the ratio streams
pop_s = Counter(); nd_meters_s = Counter(); gov_meters_s = Counter(); dom_plots_s = Counter(); dom_props_s = Counter()
row = {}
for i, f in pf.items():
    c = acc.get(i, Counter()); u = acc_gud.get(i, Counter()); s = settle[i]
    props = c['dom'] + c['dom_add']; pop = props * OR
    nd = u.get('non_domestic', 0); gv = u.get('government', 0)
    pop_s[s] += pop; nd_meters_s[s] += nd; gov_meters_s[s] += gv
    if props > 0 and f['Buiding_St'] == 'EXisting': dom_plots_s[s] += 1; dom_props_s[s] += props
    row[i] = (c, u, s, props, pop, nd, gv)
ppp_s = {s: (dom_props_s[s] / dom_plots_s[s] if dom_plots_s[s] else 0.0) for s in names}
# future capacity: future plots <= BIG_M2, not farm / industrial / proposed
cap_plots_s = Counter()
for i, f in pf.items():
    if f['Buiding_St'] == 'Future' and f.geometry().area() <= BIG_M2 and f['Classes'] not in ('Agricultural', 'Industrial', 'Proposed') and i not in estate:
        cap_plots_s[settle[i]] += 1

pfields = QgsFields()
for fn in plots.fields(): pfields.append(fn)
NEW = [('SETTLE', QVariant.String, 24), ('AREA_M2', QVariant.Double, 0), ('N_ACC', QVariant.Int, 0), ('N_DOM', QVariant.Int, 0), ('N_DOMADD', QVariant.Int, 0),
       ('N_COM', QVariant.Int, 0), ('N_GOV', QVariant.Int, 0), ('N_AGR', QVariant.Int, 0), ('N_CRT', QVariant.Int, 0), ('N_IND', QVariant.Int, 0),
       ('G_DOM', QVariant.Int, 0), ('G_NDOM', QVariant.Int, 0), ('G_GOV', QVariant.Int, 0), ('G_SPEC', QVariant.Int, 0), ('G_AGR', QVariant.Int, 0),
       ('DERIVED', QVariant.String, 24), ('WHYC', QVariant.String, 4), ('AGREE', QVariant.String, 10), ('ESTATE', QVariant.String, 10), ('WORKERS', QVariant.Double, 0),
       ('PROPS', QVariant.Int, 0), ('POP', QVariant.Double, 0),
       ('W_DOM', QVariant.Double, 0), ('W_NDOM', QVariant.Double, 0), ('W_GOV', QVariant.Double, 0), ('W_SPEC', QVariant.Double, 0), ('W_TOT', QVariant.Double, 0),
       ('S_DOM', QVariant.Double, 0), ('S_NDOM', QVariant.Double, 0), ('S_GOV', QVariant.Double, 0), ('S_SPEC', QVariant.Double, 0), ('QADF', QVariant.Double, 0),
       ('FUT_CAP', QVariant.Int, 0), ('FUT_PROPS', QVariant.Double, 0)]
for n, t, ln in NEW: pfields.append(QgsField(n, t, len=ln))
ppath = f"{W13}/shp/PLOTS_load.shp"
pw = writer(ppath, pfields, plots.wkbType(), CRS)
conf = Counter(); tot = Counter(); csvrows = []
for i, f in pf.items():
    c, u, s, props, pop, nd, gv = row[i]
    d, why = derived(i, c, u); moh = f['Classes']
    agree = 'unmetered' if d == 'Unmetered' else ('same' if d == moh else ('new' if d == 'Government' or moh == 'Proposed' else 'differs'))
    conf[(moh, d)] += 1
    wf = estate[i][1] if i in estate else 0.0
    w_dom = pop * LPCD / 1000.0                                                   # m3/d
    pool_nd = pop_s[s] * R_ND * LPCD / 1000.0; pool_gv = pop_s[s] * R_GOV * LPCD / 1000.0
    w_nd = pool_nd * nd / nd_meters_s[s] if nd_meters_s[s] else (pool_nd * pop / pop_s[s] if pop_s[s] else 0.0)
    w_gv = pool_gv * gv / gov_meters_s[s] if gov_meters_s[s] else (pool_gv * pop / pop_s[s] if pop_s[s] else 0.0)
    w_sp = wf * L_IND / 1000.0
    s_dom, s_nd, s_gv, s_sp = w_dom * RET_DOM, w_nd * RET_ND, w_gv * RET_ND, w_sp * RET_ND
    q = s_dom + s_nd + s_gv + s_sp
    is_cap = 1 if (f['Buiding_St'] == 'Future' and f.geometry().area() <= BIG_M2 and moh not in ('Agricultural', 'Industrial', 'Proposed') and i not in estate) else 0
    fut_props = ppp_s[s] if is_cap else 0.0
    vals = list(f.attributes()) + [s, round(f.geometry().area(), 1), sum(c.values()), c['dom'], c['dom_add'], c['com'], c['gov'], c['agr'], c['crt'], c['ind'],
            props, nd, gv, u.get('special', 0), u.get('agricultural', 0), d, why, agree, estate[i][0] if i in estate else '', round(wf, 1),
            props, round(pop, 2), round(w_dom, 4), round(w_nd, 4), round(w_gv, 4), round(w_sp, 4), round(w_dom + w_nd + w_gv + w_sp, 4),
            round(s_dom, 4), round(s_nd, 4), round(s_gv, 4), round(s_sp, 4), round(q, 4), is_cap, round(fut_props, 3)]
    nf = QgsFeature(pfields); nf.setGeometry(f.geometry()); nf.setAttributes(vals); pw.addFeature(nf)
    tot['pop'] += pop; tot['qadf'] += q; tot['w_tot'] += w_dom + w_nd + w_gv + w_sp
    csvrows.append([i, f['Name'], moh, f['Buiding_St'], s, round(f.geometry().area(), 1), props, round(pop, 2), nd, gv, u.get('special', 0), round(wf, 1),
                    round(w_dom, 4), round(w_nd, 4), round(w_gv, 4), round(w_sp, 4), round(s_dom, 4), round(s_nd, 4), round(s_gv, 4), round(s_sp, 4), round(q, 4), is_cap, round(fut_props, 3)])
del pw
with open(f"{W13}/analysis/plots_load_today.csv", 'w', newline='', encoding='utf-8-sig') as fh:
    cw = csv.writer(fh); cw.writerow(['fid', 'Name', 'Classes', 'Build', 'SETTLE', 'AREA_M2', 'PROPS', 'POP', 'G_NDOM', 'G_GOV', 'G_SPEC', 'WORKERS',
                                      'W_DOM', 'W_NDOM', 'W_GOV', 'W_SPEC', 'S_DOM', 'S_NDOM', 'S_GOV', 'S_SPEC', 'QADF', 'FUT_CAP', 'FUT_PROPS']); cw.writerows(csvrows)
with open(f"{W13}/analysis/settlements_today.csv", 'w', newline='', encoding='utf-8-sig') as fh:
    cw = csv.writer(fh); cw.writerow(['SETTLE', 'POP_TODAY', 'DOM_PLOTS_BUILT', 'PROPS_PER_BUILT_PLOT', 'NDOM_METERS', 'GOV_METERS', 'FREE_METERS', 'FUT_CAP_PLOTS', 'FUT_CAP_PROPS', 'FUT_CAP_POP'])
    for s in names: cw.writerow([s, round(pop_s[s]), dom_plots_s[s], round(ppp_s[s], 3), nd_meters_s[s], gov_meters_s[s], free_settle[s], cap_plots_s[s], round(cap_plots_s[s] * ppp_s[s]), round(cap_plots_s[s] * ppp_s[s] * OR)])
print('TODAY: population %.0f | water %.0f m3/d | Qadf %.0f m3/d' % (tot['pop'], tot['w_tot'], tot['qadf']))
print('agreement:', dict(Counter(a for (m, d) in conf.elements() for a in [('same' if m == d else 'diff')])))

# ---------- merged settlement boundaries: Voronoi of plot centroids, dissolved by settlement, clipped ----------
cl = QgsVectorLayer(f'Point?crs={CRS.authid()}&field=SETTLE:string(24)', 'cent', 'memory'); pr = cl.dataProvider(); feats = []
for i, f in pf.items():
    nf = QgsFeature(cl.fields()); nf.setGeometry(f.geometry().centroid()); nf.setAttributes([settle[i]]); feats.append(nf)
pr.addFeatures(feats); cl.updateExtents()
vor = processing.run('qgis:voronoipolygons', {'INPUT': cl, 'BUFFER': 10, 'OUTPUT': 'memory:'})['OUTPUT']
dis = processing.run('native:dissolve', {'INPUT': vor, 'FIELD': ['SETTLE'], 'OUTPUT': 'memory:'})['OUTPUT']
clp = processing.run('native:clip', {'INPUT': dis, 'OVERLAY': bnd, 'OUTPUT': 'memory:'})['OUTPUT']
sfields = QgsFields(); sfields.append(QgsField('SETTLE', QVariant.String, len=24)); sfields.append(QgsField('AREA_KM2', QVariant.Double))
for n, t in [('POP_TODAY', QVariant.Double), ('PPP', QVariant.Double), ('CAP_PLOTS', QVariant.Int), ('CAP_POP', QVariant.Double), ('QADF_TODAY', QVariant.Double)]: sfields.append(QgsField(n, t))
q_s = Counter()
for r in csvrows: q_s[r[4]] += r[20]
spath = f"{W13}/shp/Settlements_merged.shp"; sw = writer(spath, sfields, clp.wkbType(), CRS)
for f in clp.getFeatures():
    s = f['SETTLE']; g = QgsGeometry.unaryUnion([f.geometry(), core.get(s, QgsGeometry())]) if s in core else f.geometry()
    nf = QgsFeature(sfields); nf.setGeometry(g)
    nf.setAttributes([s, round(g.area() / 1e6, 2), round(pop_s[s]), round(ppp_s[s], 3), cap_plots_s[s], round(cap_plots_s[s] * ppp_s[s] * OR), round(q_s[s], 1)]); sw.addFeature(nf)
del sw
print('written:', mpath, ppath, spath)
