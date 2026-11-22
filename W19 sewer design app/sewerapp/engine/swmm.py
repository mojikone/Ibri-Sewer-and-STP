"""Stormwater and dynamic routing on EPA SWMM 5 (public domain), through swmm-toolkit (the SWMM 5.2.4 solver as a
Python library). SewerGEMS's "Explicit" solver is SWMM 5; this is the same public engine.

run(inp) solves a model and returns its summary; compare(out, ref) checks every time step of every link flow, node
depth and head and subcatchment runoff against a reference output (EPA's own benchmark results), at rtol 0.1 % with
atol 1e-4 in the model's units (a peak of 0.0001 is below what SWMM reports)."""
import os, shutil, tempfile
import numpy as np
from swmm.toolkit import output, shared_enum, solver

RTOL, ATOL = 1e-3, 1e-4
SERIES = [("link", shared_enum.LinkAttribute.FLOW_RATE), ("node", shared_enum.NodeAttribute.INVERT_DEPTH),
          ("node", shared_enum.NodeAttribute.HYDRAULIC_HEAD), ("subcatch", shared_enum.SubcatchAttribute.RUNOFF_RATE)]
KIND = {"subcatch": shared_enum.ElementType.SUBCATCH, "node": shared_enum.ElementType.NODE, "link": shared_enum.ElementType.LINK}


def run(inp, workdir=None):
    """Solve `inp` (its folder copied, so rain files next to it are found); returns paths, run time and summary."""
    import time
    src = os.path.dirname(os.path.abspath(inp)); workdir = workdir or tempfile.mkdtemp(prefix="w19swmm_")
    for f in os.listdir(src):
        if os.path.isfile(os.path.join(src, f)): shutil.copy(os.path.join(src, f), workdir)
    name = os.path.splitext(os.path.basename(inp))[0]
    i, r, o = (os.path.join(workdir, name + e) for e in (".inp", ".rpt", ".out"))
    t0 = time.perf_counter(); solver.swmm_run(i, r, o); dt = time.perf_counter() - t0
    return dict(inp=i, rpt=r, out=o, seconds=round(dt, 3), summary=summary(o))


def _series(h, kind, attr):
    n = output.get_proj_size(h)[{"subcatch": 0, "node": 1, "link": 2}[kind]]
    nt = output.get_times(h, shared_enum.Time.NUM_PERIODS)
    get = {"link": output.get_link_series, "node": output.get_node_series, "subcatch": output.get_subcatch_series}[kind]
    names = [output.get_elem_name(h, KIND[kind], j) for j in range(n)]
    return names, np.array([get(h, j, attr, 0, nt - 1) for j in range(n)]) if n else np.zeros((0, nt))


def _open(path):
    h = output.init(); output.open(h, path); return h


def summary(out):
    """Peak flow per link, peak depth per node, counts and periods."""
    h = _open(out)
    try:
        ln, lf = _series(h, "link", shared_enum.LinkAttribute.FLOW_RATE)
        nn, nd = _series(h, "node", shared_enum.NodeAttribute.INVERT_DEPTH)
        sn, _ = _series(h, "subcatch", shared_enum.SubcatchAttribute.RUNOFF_RATE)
        return dict(links=len(ln), nodes=len(nn), subcatchments=len(sn), periods=int(output.get_times(h, shared_enum.Time.NUM_PERIODS)),
                    peak_flow={n: float(np.abs(s).max()) for n, s in zip(ln, lf)} if len(ln) else {},
                    peak_depth={n: float(s.max()) for n, s in zip(nn, nd)} if len(nn) else {})
    finally:
        output.close(h)


def compare(out, ref):
    """Every series of `out` against `ref`: values compared, the worst relative error, and whether all are within
    tolerance. Element names must match; the periods both files hold are compared and any extra period is reported
    (some SWMM 5.2.4 builds write one more final reporting period than EPA's benchmark build)."""
    a, b = _open(out), _open(ref); rows = []
    try:
        for kind, attr in SERIES:
            na, xa = _series(a, kind, attr); nb, xb = _series(b, kind, attr)
            if na != nb:
                rows.append(dict(series=f"{kind}.{attr.name}", ok=False, why="elements differ")); continue
            if not xa.size: continue
            n = min(xa.shape[1], xb.shape[1]); extra = xa.shape[1] - xb.shape[1]
            xa, xb = xa[:, :n], xb[:, :n]
            if extra: rows.append(dict(series=f"{kind}.{attr.name} periods", ok=True, extra_periods=int(extra)))
            bad = np.abs(xa - xb) > ATOL + RTOL * np.abs(xb)
            rel = np.abs(xa - xb) / np.maximum(np.abs(xb), ATOL)
            row = dict(series=f"{kind}.{attr.name}", values=int(xa.size), outside=int(bad.sum()),
                       worst_rel=float(rel.max()), ok=not bad.any())
            if kind == "link":                       # peak flow of each link over the common periods
                pa, pb = np.abs(xa).max(axis=1), np.abs(xb).max(axis=1)
                row["peaks_outside"] = int((np.abs(pa - pb) > ATOL + RTOL * pb).sum())
                row["worst_peak_rel"] = float((np.abs(pa - pb) / np.maximum(pb, ATOL)).max())
            rows.append(row)
    finally:
        output.close(a); output.close(b)
    return dict(ok=all(r["ok"] for r in rows), series=rows)
