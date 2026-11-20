"""Every figure the final-design report text uses, read once from the results (results/final_0.75pc_SC1-SC4/), so the
text, the tables and the maps cannot disagree. Run directly to print them."""
import os, json
import pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4")
SCEN = {"SC1": ("STP-1 only", ["STP-1"]), "SC2": ("STP-2 only", ["STP-2"]), "SC3": ("STP-1 and STP-5", ["STP-1", "STP-5"]),
        "SC4": ("STP-2 and STP-5", ["STP-2", "STP-5"])}
BASE = "2056"; YEARS = ["2051", "2056", "2061"]
COST = json.load(open(os.path.join(R, "network_cost.json")))


def case(sc, y=BASE):
    c = f"{sc}-{y}"
    Q = json.load(open(os.path.join(R, c, "products", "quantities.json")))
    S = json.load(open(os.path.join(R, c, "split", f"summary_{c}.json")))
    ST = pd.read_csv(os.path.join(R, c, "products", "stations.csv"))
    K = pd.read_csv(os.path.join(R, c, "named", "links.csv"))
    P = pd.read_csv(os.path.join(R, c, "products", "plants.csv"))
    big = K[K.dn_mm > 200]; u = big[big.under075 == 1]
    net = ST[ST.kind != "plant inlet"]
    q = dict(Q)
    q.update(case=c, sc=sc, year=y, split=S, stations=ST, links=K, plants_df=P, cost=COST[c],
             km_big=big.length_m.sum() / 1000, km_under31=u.length_m.sum() / 1000,
             km_under36=big[big.v2036_ms < 0.75].length_m.sum() / 1000,
             under_by_size=(u.groupby("dn_mm").length_m.sum() / 1000).round(2).to_dict(),
             mh_over12=sum(v for b, v in Q["manholes_by_depth"].items() if b in ("12 to 15 m", "over 15 m")),
             largest=net.loc[net.duty_ls.idxmax()], longest=net.loc[net.force_main_m.idxmax()],
             v_max=S["v2056_max"], km_steepened=S["km_steepened"])
    return q


# the gradient limits compared on SC1-2056, with the same station rules (results/final_0.75pc_SC1-SC4/limits_SC1-2056/)
LIMITS = [dict(limit="0.50 %", stations=21, added=3, km_big=151.7, km_under=25.9),
          dict(limit="0.75 %", stations=23, added=5, km_big=151.4, km_under=9.3),
          dict(limit="1.00 %", stations=25, added=7, km_big=151.3, km_under=3.0)]
AS_LAID_STATIONS = 23            # SC1-2056 laid at the Table 11 minimum gradients, the same depth rules

if __name__ == "__main__":
    for sc in SCEN:
        f = case(sc)
        print(sc, f"sewers {f['sewer_km']:.0f} km, >DN200 {f['km_big']:.1f} km, under 0.75 {f['km_under31']:.1f} km, 2036 {f['km_under36']:.1f}, "
              f"pumps {f['pumps']} lifts {f['lifts']}, kW {f['kw_network']:.0f}, mh>12 {f['mh_over12']}, deepest {f['deepest']}, cost {f['cost']['total'] / 1e6:.1f} M, "
              f"largest {f['largest']['name']} {f['largest']['duty_ls']} L/s, longest {f['longest']['name']} {f['longest']['force_main_m']:.0f} m")
    f = case("SC1"); print("SC1-2056 under 0.75 by size:", f["under_by_size"])
