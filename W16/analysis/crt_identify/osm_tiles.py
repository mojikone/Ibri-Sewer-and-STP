import pandas as pd, json, urllib.request, urllib.parse, time, os, math
df = pd.read_csv("crt_points_cl.csv")
S, W, N, E = df.lat.min()-0.004, df.lon.min()-0.004, df.lat.max()+0.004, df.lon.max()+0.004
nx, ny = 6, 4
servers = ["https://overpass-api.de/api/interpreter","https://overpass-api.de/api/interpreter","https://overpass.kumi.systems/api/interpreter"]
rows = []; done = set()
if os.path.exists("osm_tiles.csv"):
    prev = pd.read_csv("osm_tiles.csv"); rows = prev.to_dict("records"); done = set(prev.tile.unique())
def body(bb):
    return (f'nwr["name"]{bb}; nwr["amenity"]{bb}; nwr["shop"]{bb}; nwr["landuse"~"industrial|commercial|retail|farmyard|quarry|military"]{bb}; '
            f'nwr["industrial"]{bb}; nwr["man_made"]{bb}; nwr["power"~"substation|plant"]{bb}; nwr["office"]{bb}; nwr["tourism"]{bb}; '
            f'nwr["leisure"]{bb}; nwr["healthcare"]{bb}; nwr["building"~"industrial|commercial|retail|warehouse|hospital|school|government|public|hotel|university|college|farm|greenhouse"]{bb};')
for iy in range(ny):
    for ix in range(nx):
        tile = f"{iy}_{ix}"
        if tile in done: continue
        s = S + (N-S)*iy/ny; n = S + (N-S)*(iy+1)/ny; w = W + (E-W)*ix/nx; e = W + (E-W)*(ix+1)/nx
        # skip tiles with no CRT points within 300 m
        m = ((df.lat>=s-0.003)&(df.lat<=n+0.003)&(df.lon>=w-0.003)&(df.lon<=e+0.003)).sum()
        if m == 0: print(tile, "empty, skipped", flush=True); done.add(tile); continue
        q = f"[out:json][timeout:90];({body(f'({s},{w},{n},{e})')});out center tags;"
        ok = False
        for attempt in range(6):
            srv = servers[attempt % len(servers)]
            try:
                t=time.time()
                with urllib.request.urlopen(urllib.request.Request(srv, data=urllib.parse.urlencode({"data":q}).encode(), headers={"User-Agent":"ibri-sewer-study/1.0"}), timeout=45) as r:
                    js = json.loads(r.read())
                for el in js["elements"]:
                    tg = el.get("tags", {}); lat = el.get("lat") or el.get("center", {}).get("lat"); lon = el.get("lon") or el.get("center", {}).get("lon")
                    if lat is None: continue
                    keys = {k: tg[k] for k in ("name","name:en","name:ar","amenity","shop","landuse","industrial","man_made","power","office","tourism","leisure","healthcare","building","craft") if k in tg}
                    rows.append(dict(tile=tile, osm=f'{el["type"]}/{el["id"]}', lat=lat, lon=lon, **keys))
                print(tile, "pts", m, "osm", len(js["elements"]), srv.split('/')[2], round(time.time()-t,1), "s", flush=True); ok = True; break
            except Exception as ex:
                print(tile, "attempt", attempt, srv.split('/')[2], "FAIL", str(ex)[:60], flush=True); time.sleep(5)
        if ok:
            pd.DataFrame(rows).to_csv("osm_tiles.csv", index=False)
        else:
            print(tile, "GAVE UP", flush=True)
print("DONE", len(rows))
