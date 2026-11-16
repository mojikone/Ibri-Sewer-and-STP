"""Subnetwork of every node (by tracing downstream to its outfall) and the transfer graph between subnetworks."""
import csv, collections, sys, json
INV = r"D:\VBOX\bridge\out\inv"
nodes = {int(r['id']): r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8'))}
links = [r for r in csv.DictReader(open(INV + r"\links.csv", encoding='utf-8')) if r['type'] == 'CO']
lab2id = {r['label']: i for i, r in nodes.items()}
down = collections.defaultdict(list)
up = collections.defaultdict(list)
for l in links:
    if l['active'] != 'True':
        continue
    s, t = int(l['start']), int(l['stop'])
    down[s].append((t, l))
    up[t].append((s, l))
multi = {n: d for n, d in down.items() if len(d) > 1}
print("nodes with >1 outgoing active conduit:", len(multi))
outfalls = {i: r for i, r in nodes.items() if r['type'] == 'OF'}
sub = {}
for oid, o in outfalls.items():
    stack = [oid]
    while stack:
        n = stack.pop()
        if n in sub:
            continue
        sub[n] = o['label']
        stack += [s for s, _ in up[n]] + [d for d, _ in down[n]]  # undirected: digitised direction is not flow direction
act_mh = [i for i, r in nodes.items() if r['type'] == 'MH' and r['active'] == 'True']
orphan = [nodes[i]['label'] for i in act_mh if i not in sub]
print("active manholes:", len(act_mh), " not reaching any outfall:", len(orphan), orphan[:10])
cnt = collections.Counter(sub[i] for i in act_mh if i in sub)
for oid, o in sorted(outfalls.items(), key=lambda kv: kv[1]['label']):
    print(f"{o['label']:6s} active={o['active']:5s} MH={cnt.get(o['label'],0):5d}  x={float(o['x']):.0f} y={float(o['y']):.0f}")
recv = {"O-4":"MH-18013","O-13":"MH-1510","O-10":"MH-1355","O-20":"MH-21582","O-7":"MH-649","O-2":"MH-14793",
        "O-15":"MH-18772","O-14":"MH-18772","O-6":"MH-14400","O-5":"MH-14400","O-19":"MH-17581","O-9":"MH-10049",
        "O-17":"MH-12700","O-16":"MH-20234","O-12":"MH-18186","O-3":"MH-15726","O-18":"MH-16127","O-22":"MH-2710",
        "O-11":"MH-9074","O-1":"MH-21598"}
print("\nreceiving manholes:")
for o, mh in recv.items():
    i = lab2id.get(mh)
    print(f"  {o:5s} -> {mh:9s} id={i}  in subnetwork {sub.get(i) if i else 'NOT FOUND'}  active={nodes[i]['active'] if i else '-'}")
json.dump({str(k): v for k, v in sub.items()}, open(INV + r"\subnet_of_node.json", "w"))
