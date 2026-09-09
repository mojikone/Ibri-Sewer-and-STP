import pandas as pd, numpy as np, re, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
pts = pd.read_csv("crt_points_osm.csv"); pts['osm_near'] = pts.osm_near.fillna('')
nom = pd.read_csv("nominatim.csv")
nom_pt = nom[nom.kind == 'pt'].set_index('key')

# cluster verdicts: (use, evidence, confidence)
C = {
 78: ('Commercial', 'Ibri Bawadi Mall / Lulu Hypermarket, Chicking (Google sat + OSM)', 'Certain'),
 106: ('Commercial', 'Souq street Al Murtafa: bookshop, Marjan supermarket, polyclinic (OSM + Google)', 'Certain'),
 64: ('Commercial', 'Shop strip along Al Ghabbi dual carriageway (Google sat)', 'Likely'),
 127: ('Government', 'Ibri Police Station, Al Akhdar (Nominatim nearest)', 'Likely'),
 132: ('Government', 'Ibri Police Station, Al Akhdar (Nominatim nearest)', 'Likely'),
 69: ('Commercial', 'Sana Ibri Shopping, Nizwa Islamic Bank, Araqi strip (Google)', 'Certain'),
 70: ('Commercial', 'Araqi commercial strip, next to cluster 69 (Google)', 'Likely'),
 71: ('Commercial', 'Araqi commercial strip, next to cluster 69 (Google)', 'Likely'),
 67: ('Commercial', 'Araqi strip, road D618 (Nominatim)', 'Guessing'),
 68: ('Commercial', 'Araqi strip (Nominatim)', 'Guessing'),
 96: ('Commercial', 'Al Murtafa, dual carriageway frontage, walled compound (Google sat)', 'Guessing'),
 81: ('Education', 'UTAS Ibri Al Akhdar campus, D Building, storage (OSM + Nominatim)', 'Likely'),
 116: ('Commercial', 'Al Yamama shopping centre (OSM, 2 m)', 'Certain'),
 65: ('Agricultural', 'Aynayn farms, agricultural plots, Time-of-Use tariff = pumping (Google sat)', 'Likely'),
 120: ('Commercial', 'Al Fawar and Tayyibat Al Sham restaurants, Bake it Bakery, Al Akhdar (OSM)', 'Certain'),
 21: ('Government', 'Ibri Police Headquarters campus, Bu Khabi (Nominatim + Google sat)', 'Likely'),
 16: ('Government', 'Ibri Police Headquarters (Nominatim)', 'Likely'),
 18: ('Government', 'Ibri Police Headquarters (Nominatim)', 'Likely'),
 35: ('Industrial', 'Al Mukhtobiyah industrial estate, warehouses, Industrial plots (Google sat)', 'Certain'),
 6: ('Commercial', 'Riad Al Driz Shopping Center, Ad Dariz (OSM)', 'Certain'),
 1: ('Health', 'Horizons Medical, veterinary, Ad Dariz (OSM)', 'Likely'),
 14: ('Government', 'Fenced compound of blue-roofed halls next to Police HQ, Bu Khabi (Google sat)', 'Guessing'),
 175: ('Commercial', 'MAYSA national shopping, Bat village centre (OSM + Google)', 'Likely'),
 135: ('Commercial', 'Omantel office, Oxygen Pharmacy, Hayy Almazra (OSM)', 'Certain'),
 156: ('Unresolved', 'Al Orobah, parking + mosque nearby only (OSM)', 'Guessing'),
 153: ('Unresolved', 'Al Orobah, parking only (OSM)', 'Guessing'),
 157: ('Unresolved', 'Al Orobah, parking only (OSM)', 'Guessing'),
 154: ('Unresolved', 'Al Orobah, Ibri Road, Proposed plots', 'Guessing'),
 149: ('Commercial', 'A SSFA, between Al Hashar Automotive and Ramez hypermarket strip (OSM)', 'Guessing'),
 139: ('Commercial', 'Al Hashar Automotive, Al-huad Pharmacy, Muscat Bank, Oman Oil (OSM)', 'Certain'),
 137: ('Commercial', 'Makkah Hypermarket, Ramez Hypermarket (OSM)', 'Certain'),
 128: ('Commercial', 'A SSFA, Res-Com plots on Sultan Thuwaini road', 'Guessing'),
 54: ('Health', 'Ibri Hospital (Nominatim nearest)', 'Likely'),
 58: ('Government', 'Al Ghabbi, health complex / chamber of commerce compound near Lulu north (Google label)', 'Guessing'),
 57: ('Commercial', 'LuLu Hypermarket Silmi, CRT Fixed Rate (OSM 45 m)', 'Certain'),
 50: ('Education', 'College of Technology, Saih Al Masarrat (Nominatim)', 'Likely'),
 30: ('Unresolved', 'Isolated buildings on Commercial plots east of Araqi (Google sat)', 'Guessing'),
 33: ('Unresolved', 'Mazra bin Khater, Ibri - Rub al Khali road', 'Guessing'),
 92: ('Unresolved', 'Hellat As sad, residential', 'Guessing'),
 110: ('Unresolved', 'Silmi, residential', 'Guessing'),
 122: ('Unresolved', 'Ibri Old village', 'Guessing'),
 87: ('Unresolved', 'As Sulayf', 'Guessing'),
 126: ('Commercial', 'Morgan Muscat Bakery and Market, Hellat Al Nahadah (OSM 18 m)', 'Likely'),
 102: ('Commercial', 'Retail building + Shell fuel, Hayy Almazra (OSM)', 'Likely'),
 79: ('Government', 'Al Akhdar Post Office, Health Center, Directorate-General for Education (OSM)', 'Certain'),
 80: ('Religious', 'College Mosque, Al Akhdar (OSM 14 m)', 'Likely'),
 113: ('Education', 'Ibri basic education school for girls 5-9 (OSM)', 'Likely'),
 95: ('Commercial', 'Pizza Hut, Al Murtafa (OSM)', 'Certain'),
 136: ('Education', 'Indian School Ibri (OSM 40 m)', 'Likely'),
 138: ('Commercial', 'Photographer, Muscat Pharmacy, Ibri Road (OSM)', 'Likely'),
 145: ('Telecom/Utility', 'PBX connections building, Ibri Old village (OSM)', 'Likely'),
 130: ('Commercial', 'Karama Building Materials, MAX (OSM)', 'Certain'),
}

RULES = [
    ('Religious', r'place_of_worship|mosque|مسجد|جامع|مصلى'),
    ('Education', r'school|college|مدرسة|university|التدريب'),
    ('Health', r'hospital|pharmacy|doctors|clinic|medical|تأهيل'),
    ('Government', r'police|government|directorate|municipal|بلدية|chamber of commerce|manpower|stadium'),
    ('Telecom/Utility', r'water_works|tower|omantel|pbx|substation'),
    ('Industrial', r'industrial|mot centre|warehouse'),
    ('Commercial', r'shop|supermarket|restaurant|fast_food|bank|atm|fuel|car_wash|insurance|convenience|variety|retail|commercial|juice|مطعم|مقهى|نفط|هايبر'),
]

def single_rule(p):
    s = p.osm_near.split(' | ')[0] if p.osm_near else ''
    n = nom_pt.loc[p.fid] if p.fid in nom_pt.index else None
    nm = str(n['name']) if n is not None and pd.notna(n['name']) else ''
    ty = str(n['type']) if n is not None and pd.notna(n['type']) else ''
    txt = (s + ' ' + nm + ' ' + ty).lower()
    for use, rx in RULES:
        if re.search(rx, txt):
            ev = s if s else f"{nm} ({ty}, Nominatim)"
            return use, ev, ('Likely' if s else 'Guessing')
    sub = str(n['suburb']) if n is not None and pd.notna(n['suburb']) else ''
    if p.plot_class == 'Agricultural':
        return 'Agricultural', f'Agricultural plot, {sub} (no POI within 80 m)', 'Guessing'
    if p.plot_class == 'Industrial':
        return 'Industrial', f'Industrial plot, {sub}', 'Likely'
    return 'Unresolved', (f'{sub}: no POI within 80 m' if sub else 'no POI within 80 m'), 'Guessing'

use, ev, conf = [], [], []
for _, p in pts.iterrows():
    if p.cl in C:
        u, e, c = C[p.cl]
    else:
        u, e, c = single_rule(p)
    if p.tariff == 'Industrial':
        u, e, c = 'Industrial', 'Industrial tariff; ' + e, 'Certain'
    use.append(u); ev.append(e); conf.append(c)
pts['USE'] = use; pts['EVIDENCE'] = ev; pts['CONF'] = conf
gud = {'Commercial': 'non_domestic', 'Government': 'government', 'Education': 'government', 'Health': 'government',
       'Religious': 'government', 'Telecom/Utility': 'non_domestic', 'Industrial': 'industrial',
       'Agricultural': 'agricultural', 'Unresolved': 'CRT_review'}
pts['GUD_CAT'] = pts.USE.map(gud)
out = pts[['fid', 'tariff', 'lon', 'lat', 'cl', 'plot_name', 'plot_class', 'USE', 'GUD_CAT', 'CONF', 'EVIDENCE']]
dst = "D:/Mojtaba/Renardet/2621 Ibri Sewer STP/Hydraulic/Claude/W13/analysis/CRT_accounts_identified.csv"
out.to_csv(dst, index=False, encoding='utf-8-sig')
print(pd.crosstab(pts.USE, pts.CONF, margins=True))
print()
print(pts.groupby('USE').tariff.value_counts().unstack(fill_value=0))
print("\nGUD_CAT:", pts.GUD_CAT.value_counts().to_dict())
