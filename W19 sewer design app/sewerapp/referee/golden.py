"""Comparisons of a case folder with W18's frozen outputs. case_differences: every file, numerically exact to rtol.
engineering_differences: the spec's phase-1 tolerances (section 7)."""
import json, math, os
import numpy as np, pandas as pd
from sewerapp import fixtures

FILES = ["named/links.csv", "named/nodes.csv", "named/stations.csv", "products/stations.csv", "products/plants.csv",
         "selfcleansing_pipes.csv", "split/cuts_{c}.csv", "split/joins_{c}.csv", "exports/conduits_{c}a.csv",
         "exports/transfers_{c}.csv", "exports/lift_transfers_{c}.csv"]
JSONS = ["design.json", "products/quantities.json", "named/naming.json", "split/summary_{c}.json"]


def frame_differences(name, a, b, rtol=1e-9, atol=1e-9):
    if list(a.columns) != list(b.columns): return [f"{name}: columns {list(a.columns)} != {list(b.columns)}"]
    if len(a) != len(b): return [f"{name}: {len(a)} rows != {len(b)}"]
    out = []
    for col in a.columns:
        x, y = a[col].to_numpy(), b[col].to_numpy()
        if np.issubdtype(x.dtype, np.number) and np.issubdtype(y.dtype, np.number):
            bad = ~np.isclose(x.astype(float), y.astype(float), rtol=rtol, atol=atol, equal_nan=True)
        else:
            bad = (pd.Series(x).astype(str) != pd.Series(y).astype(str)).to_numpy()
        if bad.any():
            i = int(np.flatnonzero(bad)[0])
            out.append(f"{name}: column {col}, {int(bad.sum())} rows differ, first row {i}: {x[i]!r} != {y[i]!r}")
    return out


def json_differences(name, a, b, rtol=1e-9, atol=1e-9, where=""):
    if isinstance(a, dict) and isinstance(b, dict):
        if set(a) != set(b): return [f"{name}{where}: keys {sorted(set(a) ^ set(b))} differ"]
        return [d for k in a for d in json_differences(name, a[k], b[k], rtol, atol, f"{where}.{k}")]
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b): return [f"{name}{where}: length {len(a)} != {len(b)}"]
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in json_differences(name, x, y, rtol, atol, f"{where}[{i}]")]
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return [] if math.isclose(a, b, rel_tol=rtol, abs_tol=atol) else [f"{name}{where}: {a} != {b}"]
    return [] if a == b else [f"{name}{where}: {a!r} != {b!r}"]


def case_differences(case_dir, case, rtol=1e-9, atol=1e-9):
    out = []
    for f in FILES:
        rel = f.format(c=case)
        a, b = pd.read_csv(os.path.join(case_dir, rel)), fixtures.read_csv(f"golden/{case}/{rel}")
        if rel == "named/links.csv":            # row order follows Python's per-process hash seed; compare by key
            a = a.sort_values("key", kind="stable").reset_index(drop=True)
            b = b.sort_values("key", kind="stable").reset_index(drop=True)
        out += frame_differences(rel, a, b, rtol, atol)
    for f in JSONS:
        rel = f.format(c=case)
        mine = json.load(open(os.path.join(case_dir, rel), encoding="utf-8"))
        gold = json.load(open(fixtures.path(f"golden/{case}/{rel}"), encoding="utf-8"))
        out += json_differences(rel, mine, gold, rtol, atol)
    return out


def engineering_differences(case_dir, case):
    """Identical sizes, depths +-1 mm, flows 0.1 %, the same stations at the same manholes, the same km under 0.75 m/s
    at 2031 and 2036 (+-0.01 km), the same deepest manhole (+-1 mm)."""
    out = []
    a = pd.read_csv(os.path.join(case_dir, "named", "links.csv")).set_index("key")
    b = fixtures.read_csv(f"golden/{case}/named/links.csv").set_index("key")
    if not a.index.equals(b.index): return [f"links: different pipe keys ({len(a)} vs {len(b)})"]
    n = int((a.dn_mm != b.dn_mm).sum())
    if n: out.append(f"size: {n} pipes differ, first {a.index[a.dn_mm != b.dn_mm][0]}")
    for col in ("depth_up_m", "depth_dn_m"):
        n = int(((a[col] - b[col]).abs() > 0.001 + 1e-9).sum())
        if n: out.append(f"{col}: {n} pipes beyond 1 mm")
    qa = pd.read_csv(os.path.join(case_dir, "exports", f"conduits_{case}a.csv")).set_index("label").flow_m3d
    qb = fixtures.read_csv(f"golden/{case}/exports/conduits_{case}a.csv").set_index("label").flow_m3d.reindex(qa.index)
    rel = ((qa - qb).abs() / qb).fillna(0)
    if (rel > 0.001).any(): out.append(f"flow: {int((rel > 0.001).sum())} pipes beyond 0.1 %, largest {rel.max() * 100:.3f} %")
    cols = ["name", "old", "kind", "system", "pumps_to"]
    sa = pd.read_csv(os.path.join(case_dir, "named", "stations.csv"))[cols]
    sb = fixtures.read_csv(f"golden/{case}/named/stations.csv")[cols]
    if not sa.equals(sb): out.append("stations: the list differs")
    ja = json.load(open(os.path.join(case_dir, "products", "quantities.json")))
    jb = json.load(open(fixtures.path(f"golden/{case}/products/quantities.json")))
    for k in ("km_big_under075_2031", "km_big_under075_2036"):
        if abs(ja[k] - jb[k]) > 0.01: out.append(f"{k}: {ja[k]} vs {jb[k]}")
    if ja["deepest"]["name"] != jb["deepest"]["name"] or abs(ja["deepest"]["depth"] - jb["deepest"]["depth"]) > 0.001:
        out.append(f"deepest: {ja['deepest']} vs {jb['deepest']}")
    return out
