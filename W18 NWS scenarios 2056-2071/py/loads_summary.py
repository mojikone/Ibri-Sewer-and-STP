"""The sanitary load of every model year, split into what the 24 subnetworks carry and what sits on manholes outside
them (the three deactivated outlying catchments and the other inactive manholes), with the infiltration of the active
network. Written once for the report (results/loads_by_year.json), read by W17/report/facts_w17.py.

    python loads_summary.py
Source: the model's sanitary rows per manhole and year (D:\\VBOX\\bridge\\out\\r4\\diag\\rows_<year>.csv, the R4_loads
model: one row per manhole, equal to the plot layer to the decimal) and the active conduits of the 2070 design inputs.
"""
import csv, json, collections
from routing import YEARS

DIAG = r"D:\VBOX\bridge\out\r4\diag"
S1 = r"D:\VBOX\bridge\out\scen\S1"
OUT = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Hydraulic\Claude\W17\results\loads_by_year.json"
SUB = lambda lab: lab.split("-")[0] if lab.startswith("O") and ("-M" in lab or "-P" in lab) else None

km = sum(float(r["length_m"]) for r in csv.DictReader(open(rf"{S1}\conduits_base2070_inputs.csv", encoding="utf-8"))
         if r["active"] == "True" and SUB(r["label"])) / 1000
res = dict(active_sewer_km=round(km, 3), infiltration_m3d=round(km * 0.72, 1), years={})
for y in YEARS:
    tot = carried = 0.0; outside = collections.Counter()
    for r in csv.DictReader(open(rf"{DIAG}\rows_{y}.csv", encoding="utf-8")):
        q = float(r["base_m3d"]); tot += q
        if SUB(r["label"]):
            carried += q
        else:
            outside[r["label"]] += q
    res["years"][y] = dict(plot_load_m3d=round(tot, 1), carried_m3d=round(carried, 1),
                           outside_m3d=round(tot - carried, 1), outside_manholes=len(outside))
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1)
print(json.dumps(res, indent=1))
