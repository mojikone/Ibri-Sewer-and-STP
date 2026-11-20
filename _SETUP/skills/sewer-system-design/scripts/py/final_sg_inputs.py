"""W18 final design: the inputs that turn the SewerGEMS model R4 into one case of the final design (job 079 onwards,
bridge lib/FinalBuild.cs). Everything in the model's own element ids; elevations in metres.
  conduits.csv  every conduit of the network: id, active (a lift's pipe to the next manhole becomes its force main and is
                switched off), size label, start and stop inverts in the model's start/stop order, new label
  manholes.csv  id, invert (the lowest invert at the manhole), new label
  outfalls.csv  every outfall: id, active (an outfall joined by gravity is switched off), invert, new label
  lifts.csv     station manhole id, lift name, x, y, ground, invert, the size of the stub to the lift's outfall
  joins.csv     the joined outfall id, the new manhole (label, x, y, ground, invert), the new sewer to the receiving
                manhole (label, receiver id, size, length, up and down inverts)
  transfers.csv year, source, receiver id, receiver label, m3/d: the pumps that are still pumped and the lifts
Usage: python final_sg_inputs.py SC1-2056    Writes D:\\VBOX\\bridge\\in\\final\\<case>\\ and a copy in <case>/sewergems/inputs."""
import os, sys, io, json, tempfile, contextlib, shutil
import numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); W18 = os.path.dirname(HERE)
CASE = sys.argv[1]; NAME, YEAR = CASE.split("-")
R = os.path.join(W18, "results", "final_0.75pc_SC1-SC4"); EXP = os.path.join(R, CASE, "exports")
OUT = rf"D:\VBOX\bridge\in\final\{CASE}"; os.makedirs(OUT, exist_ok=True)
sys.argv = ["split_deep_subnetworks.py", CASE, EXP, os.path.join(tempfile.gettempdir(), f"w18_sg_{CASE}"), "0.0075",
            "--fixed=" + os.path.join(R, "fixed_stations.json")]
sys.path.insert(0, HERE)
with contextlib.redirect_stdout(io.StringIO()):
    import split_deep_subnetworks as T
act = set(T.best["active"]); L = T.links; li = T.best["li"]; inv = T.best["inv"]; lab = T.lab
links_new = pd.read_csv(os.path.join(R, CASE, "named", "links.csv")).set_index("old").new.to_dict()
nodes = pd.read_csv(os.path.join(R, CASE, "named", "nodes.csv")); new_of = nodes.set_index("id").new.to_dict()
st = pd.read_csv(os.path.join(R, CASE, "named", "stations.csv")); name_of = st.set_index("old").name.to_dict()
ex = pd.read_csv(os.path.join(EXP, f"conduits_{CASE}a.csv")).set_index("id")
cut = {c["link"]: L[c["link"]]["up"] for c in T.best["cuts"]}

rows = []
for k in [k for k in L if L[k]["kind"] == "pipe"]:
    l = L[k]; sid = int(T.dy.at[k, "id"]); r = ex.loc[sid]; up_is_start = r.start == l["up"]
    if k in act: u, d = li[k]
    else: u, d = inv.get(l["up"], np.nan), inv.get(l["up"], np.nan) - l["S"] * l["L"]
    rows.append(dict(id=sid, active=int(k in act), size=f"{int(l['nom'])} mm", start_inv=round(u if up_is_start else d, 4), stop_inv=round(d if up_is_start else u, 4),
                     label=links_new.get(l["label"], f"{name_of[lab[l['up']]]}-RM" if k in cut else l["label"])))
C = pd.DataFrame(rows); C.to_csv(os.path.join(OUT, "conduits.csv"), index=False)
mh = [dict(id=n, invert=round(inv[n], 4), label=new_of.get(n, lab.get(n))) for n in T.mh.index if n in inv]
pd.DataFrame(mh).to_csv(os.path.join(OUT, "manholes.csv"), index=False)
# a gravity join is carried in the model as a transfer to the receiving manhole (as the design sized it, not re-peaked):
# SewerGEMS 10.4 did not solve the new sewers of the two large joins created through the API (job 080: 0.305 m depth
# and 5-7 m/s in both, with the backwater of the headloss 20 pipes upstream); the short sewers stay in GIS and the BOQ
JOINS_AS_TRANSFERS = True
joined = set() if JOINS_AS_TRANSFERS else {j["terminal"] for j in T.best["joins"]}
of = [dict(id=n, active=int(n not in joined), invert=round(inv.get(n, np.nan), 4), label=new_of.get(n, lab[n])) for n in T.orig_terminals]
pd.DataFrame(of).to_csv(os.path.join(OUT, "outfalls.csv"), index=False)
lf = []
for k, n in cut.items():
    into_sizes = [L[j]["nom"] for j in act if L[j]["dn"] == n]
    lf.append(dict(station_id=n, name=name_of[lab[n]], x=T.xy[n][0], y=T.xy[n][1], ground=round(T.ground[n], 3), invert=round(inv[n], 4),
                   stub_size=f"{int(max(into_sizes or [200]))} mm", cut_id=int(T.dy.at[k, "id"])))
pd.DataFrame(lf).to_csv(os.path.join(OUT, "lifts.csv"), index=False)
jn = []
for j in ([] if JOINS_AS_TRANSFERS else T.best["joins"]):
    k = ("join", j["source"]); n = j["terminal"]; u, d = li[k]
    jn.append(dict(outfall_id=n, mh_label=new_of[n], x=T.xy[n][0], y=T.xy[n][1], ground=round(T.ground[n], 3), invert=round(inv[n], 4),
                   pipe_label=links_new[L[k]["label"]], receiver_id=j["receiver"], size=f"{int(L[k]['nom'])} mm", length=round(L[k]["L"], 2),
                   up_inv=round(u, 4), dn_inv=round(d, 4)))
pd.DataFrame(jn, columns=["outfall_id", "mh_label", "x", "y", "ground", "invert", "pipe_label", "receiver_id", "size", "length", "up_inv", "dn_inv"]).to_csv(os.path.join(OUT, "joins.csv"), index=False)
tr = pd.read_csv(os.path.join(EXP, f"transfers_{CASE}.csv"))
tr = tr if JOINS_AS_TRANSFERS else tr[~tr.source.isin([j["source"] for j in T.best["joins"]])]
ltr = pd.read_csv(os.path.join(EXP, f"lift_transfers_{CASE}.csv"))
pipe_up = {L[k]["label"]: L[k]["up"] for k in cut}
ltr = pd.DataFrame(dict(year=ltr.year, source=[name_of[lab[pipe_up[p]]] for p in ltr.cut_pipe], receiver_id=ltr.receiver_id,
                        receiver_label=[new_of.get(r, lab.get(r)) for r in ltr.receiver_id], flow_m3d=ltr.flow_m3d))
tr = tr.assign(receiver_label=[new_of.get(r, l) for r, l in zip(tr.receiver_id, tr.receiver_label)])
pd.concat([tr, ltr]).to_csv(os.path.join(OUT, "transfers.csv"), index=False)
dst = os.path.join(R, CASE, "sewergems", "inputs"); shutil.rmtree(dst, ignore_errors=True); shutil.copytree(OUT, dst)
print(json.dumps(dict(case=CASE, conduits=len(C), inactive=int((C.active == 0).sum()), manholes=len(mh), outfalls=len(of),
                      outfalls_off=int(sum(1 for o in of if not o["active"])), lifts=len(lf), joins=len(jn), transfer_rows=len(tr) + len(ltr))))
