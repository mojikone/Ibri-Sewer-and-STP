"""Public climate record for the study-area section: NASA POWER, at the existing STP.

NASA POWER (power.larc.nasa.gov) serves the MERRA-2 reanalysis free of restriction. It is a
modelled record on a grid of about 50 km, not a station: good for the monthly regime and the
prevailing wind, not for the dispersion modelling of the odour buffer, which needs the station.

    daily   2001-2024   T2M, T2M_MAX, T2M_MIN (deg C at 2 m), PRECTOTCORR (mm/day)
    hourly  2015-2024   WS10M (m/s), WD10M (degrees the wind blows FROM), local solar time

    python fetch_climate_power.py
"""
import csv, json, os, time, urllib.request
from pyproj import Transformer

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "climate")
STP_E, STP_N = 444387.0, 2563352.0          # existing STP, EPSG:32640
LON, LAT = Transformer.from_crs(32640, 4326, always_xy=True).transform(STP_E, STP_N)
BASE = "https://power.larc.nasa.gov/api/temporal"


def get(url):
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Renardet-2621-Ibri-report/1.0"}), timeout=300) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:
            print("   retry", attempt + 1, e); time.sleep(10)
    raise RuntimeError(url)


def daily(y0=2001, y1=2024):
    url = (f"{BASE}/daily/point?parameters=T2M,T2M_MAX,T2M_MIN,PRECTOTCORR&community=AG&longitude={LON:.4f}&latitude={LAT:.4f}"
           f"&start={y0}0101&end={y1}1231&format=JSON")
    d = get(url); p = d["properties"]["parameter"]
    path = os.path.join(OUT, f"power_daily_{y0}_{y1}.csv")
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["date", "t_mean_c", "t_max_c", "t_min_c", "rain_mm"])
        for k in sorted(p["T2M"]):
            w.writerow([f"{k[:4]}-{k[4:6]}-{k[6:]}", p["T2M"][k], p["T2M_MAX"][k], p["T2M_MIN"][k], p["PRECTOTCORR"][k]])
    print("wrote", path, len(p["T2M"]), "days |", d["header"]["title"], "|", d["header"].get("sources"))
    return d["geometry"]["coordinates"]


def hourly(y0=2015, y1=2024):
    path = os.path.join(OUT, f"power_hourly_wind_{y0}_{y1}.csv")
    n = 0
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(["time_lst", "ws10m_ms", "wd10m_deg"])
        for y in range(y0, y1 + 1):
            url = (f"{BASE}/hourly/point?parameters=WS10M,WD10M&community=RE&longitude={LON:.4f}&latitude={LAT:.4f}"
                   f"&start={y}0101&end={y}1231&format=JSON&time-standard=lst")
            p = get(url)["properties"]["parameter"]
            for k in sorted(p["WS10M"]):
                w.writerow([f"{k[:4]}-{k[4:6]}-{k[6:8]} {k[8:]}:00", p["WS10M"][k], p["WD10M"][k]]); n += 1
            print("   ", y, len(p["WS10M"]), "hours"); time.sleep(2)
    print("wrote", path, n, "hours")


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    print(f"point: lon {LON:.4f}, lat {LAT:.4f}")
    cell = daily()
    print("grid cell reported:", cell)
    hourly()
    with open(os.path.join(OUT, "SOURCE.txt"), "w", encoding="utf-8") as fh:
        fh.write("NASA Prediction Of Worldwide Energy Resources (POWER), MERRA-2 reanalysis, https://power.larc.nasa.gov\n"
                 f"Point: lon {LON:.4f}, lat {LAT:.4f} (the existing STP). Downloaded {time.strftime('%Y-%m-%d')}.\n"
                 "Daily 2001-2024: T2M, T2M_MAX, T2M_MIN, PRECTOTCORR. Hourly 2015-2024: WS10M, WD10M, local solar time.\n"
                 "A modelled record on a grid of about 50 km, not a station.\n")
