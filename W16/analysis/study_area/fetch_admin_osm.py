"""Administrative outlines for the locator inset of the location map, from OpenStreetMap.

OpenStreetMap is used because it is the current record: geoBoundaries (checked 2026-09-17) still
carries Oman as the 7 regions of 2010, and the country has had 11 governorates since 2011.
The governorates of Oman (admin_level 4), and the Wilayat of Ibri (admin_level 6), are written
as GeoJSON in WGS 84 with the date of download. Licence: ODbL, "© OpenStreetMap contributors".

    python fetch_admin_osm.py
"""
import json, os, time, datetime, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "admin")
UA = "Renardet-2621-Ibri-report/1.0 (mojikoneai@gmail.com)"
OMAN = 305138            # relation: Oman, admin_level 2
IBRI = 19563440          # relation: Wilayat of Ibri, admin_level 6


def get(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read().decode("utf-8")


# The eleven governorates in force since Royal Decree 114/2011.
GOVERNORATES = ["Muscat", "Dhofar", "Musandam", "Al Buraimi", "Ad Dakhiliyah", "Al Batinah North", "Al Batinah South",
                "Ash Sharqiyah North", "Ash Sharqiyah South", "Ad Dhahirah", "Al Wusta"]


def governorate_ids():
    """The relation of every governorate, found by name through Nominatim (the Overpass servers
    timed out on 2026-09-17). Only an administrative boundary at admin_level 4 is accepted."""
    found = {}
    for name in GOVERNORATES:
        url = ("https://nominatim.openstreetmap.org/search?format=jsonv2&limit=6&extratags=1&accept-language=en&countrycodes=om&q="
               + urllib.parse.quote(f"{name} Governorate, Oman"))
        hits = [r for r in json.loads(get(url)) if r.get("osm_type") == "relation" and r.get("type") == "administrative"
                and (r.get("extratags") or {}).get("admin_level") == "4"]
        if not hits:
            raise RuntimeError(f"no admin_level 4 relation found for {name}")
        found[hits[0]["osm_id"]] = {"name:en": f"{name} Governorate", "name": hits[0].get("name")}
        print(f"   {name:22s} relation {hits[0]['osm_id']}  {hits[0].get('display_name', '')[:60]}")
        time.sleep(1.2)
    if len(found) != len(GOVERNORATES):
        raise RuntimeError("two names resolved to one relation")
    return found


def polygons(ids, threshold=0.003):
    """Nominatim returns the assembled polygon of a relation; the threshold thins it for a small inset."""
    feats = []
    ids = list(ids)
    for k in range(0, len(ids), 40):
        chunk = ",".join(f"R{i}" for i in ids[k:k + 40])
        url = ("https://nominatim.openstreetmap.org/lookup?format=geojson&polygon_geojson=1"
               f"&polygon_threshold={threshold}&extratags=1&namedetails=1&accept-language=en&osm_ids={chunk}")
        feats += json.loads(get(url))["features"]
        time.sleep(1.5)
    return feats


def main():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()
    gov = governorate_ids()
    print(len(gov), "governorates:", sorted(t.get("name:en", t.get("name", "?")) for t in gov.values()))
    fg = polygons(gov)
    for f in fg:
        p = f["properties"]; t = gov.get(p.get("osm_id"), {})
        f["properties"] = {"osm_id": p.get("osm_id"), "name_en": t.get("name:en") or (p.get("namedetails") or {}).get("name:en") or p.get("name"),
                           "name_ar": t.get("name"), "admin_level": 4, "downloaded": today, "source": "OpenStreetMap contributors, ODbL"}
    fi = polygons([IBRI], threshold=0.0008)
    for f in fi:
        f["properties"] = {"osm_id": IBRI, "name_en": "Wilayat of Ibri", "admin_level": 6, "downloaded": today,
                           "source": "OpenStreetMap contributors, ODbL"}
    for name, feats in (("oman_governorates_osm.geojson", fg), ("ibri_wilayat_osm.geojson", fi)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            json.dump({"type": "FeatureCollection", "features": feats}, fh, ensure_ascii=False)
        print("wrote", name, len(feats), "features,", os.path.getsize(os.path.join(OUT, name)) // 1024, "KB")


if __name__ == "__main__":
    main()
