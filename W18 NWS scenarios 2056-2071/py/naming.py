"""Outfall, manhole and conduit renaming map (trunk first, then branches; a pipe takes its upstream manhole's number).
Trunk = at every junction, follow the branch with the most manholes upstream."""
import csv, collections, sys
sys.setrecursionlimit(100000)
INV = r"D:\VBOX\bridge\out\inv"
nodes = {int(r['id']): r for r in csv.DictReader(open(INV + r"\nodes.csv", encoding='utf-8'))}
links = [r for r in csv.DictReader(open(INV + r"\links.csv", encoding='utf-8')) if r['type'] == 'CO']
lab2id = {r['label']: i for i, r in nodes.items()}

# old outfall label -> new number, in the agreed order (O-21 assumed to drain into the O-1 subnetwork)
ORDER = ["O-1",
         "O-21", "O-2", "O-7", "O-20", "O-13", "O-4", "O-10",          # towards O-4
         "O-3", "O-16", "O-17", "O-9", "O-19", "O-12", "O-18",          # towards O-19
         "O-8", "O-23", "O-24", "O-11", "O-22",                         # south
         "O-6", "O-14", "O-15", "O-5"]                                  # west
NEW = {old: f"O{i+1}" for i, old in enumerate(ORDER)}

adj = collections.defaultdict(list)
for l in links:
    if l['active'] != 'True':
        continue
    s, t = int(l['start']), int(l['stop'])
    adj[s].append((t, int(l['id'])))
    adj[t].append((s, int(l['id'])))

rows_n, rows_l, problems = [], [], []
for old in ORDER:
    root = lab2id[old]
    # BFS tree from the outfall
    parent, pedge, order = {root: None}, {}, [root]
    q = collections.deque([root]); nedges = 0
    while q:
        n = q.popleft()
        for m, eid in adj[n]:
            nedges += 1
            if m not in parent:
                parent[m] = n; pedge[m] = eid; order.append(m); q.append(m)
    nedges //= 2
    if nedges != len(order) - 1:
        problems.append(f"{old}: {len(order)} nodes but {nedges} edges (loop)")
    children = collections.defaultdict(list)
    for m in order[1:]:
        children[parent[m]].append(m)
    size = {}
    for n in reversed(order):
        size[n] = 1 + sum(size[c] for c in children[n])
    num = {}
    counter = [0]
    def number_path(start):
        path, n = [], start
        while True:
            path.append(n)
            kids = sorted(children[n], key=lambda c: -size[c])
            if not kids:
                break
            n = kids[0]
        side = []
        for n in path:
            counter[0] += 1; num[n] = counter[0]
            for c in sorted(children[n], key=lambda c: -size[c])[1:]:
                side.append(c)
        for c in side:
            number_path(c)
    first = children[root]
    if len(first) != 1:
        problems.append(f"{old}: outfall has {len(first)} incoming pipes")
    for c in sorted(first, key=lambda c: -size[c]):
        number_path(c)
    new = NEW[old]
    rows_n.append((root, old, new))
    for n, k in num.items():
        rows_n.append((n, nodes[n]['label'], f"{new}-M{k}"))
        rows_l.append((pedge[n], next(l['label'] for l in [] ) if False else None, f"{new}-P{k}"))
lab_of_link = {int(l['id']): l['label'] for l in links}
rows_l = [(e, lab_of_link[e], new) for e, _, new in rows_l]
with open(INV + r"\rename_nodes.csv", "w", newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(["id", "old", "new"]); w.writerows(rows_n)
with open(INV + r"\rename_links.csv", "w", newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(["id", "old", "new"]); w.writerows(rows_l)
print("nodes renamed:", len(rows_n), " links renamed:", len(rows_l))
print("problems:", problems or "none")
for old in ORDER:
    print(f"  {old:5s} -> {NEW[old]}")
