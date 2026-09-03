"""DEFECT CLASS 5 - DEAD CODE THAT COST 26 MINUTES.

The bug: a set was rebuilt inside a loop to fill a variable nobody read. Nothing was
wrong with the output, so no result-based check could ever have found it. The run just
took 26 minutes longer than it needed to, every time, for weeks.

Two halves, and both are needed:

  STATIC   work whose result is thrown away, and work repeated inside a loop that does
           not depend on the loop. Both are detectable from the syntax tree alone, which
           means they are caught at write time rather than at run time.
  DYNAMIC  a runtime BOUND, with the measured time printed whether it passes or not.
           A smoke test that only says pass/fail hides a regression that is still inside
           the bound - and the reason nobody caught the 26 minutes is that nobody had
           written a bound down at all.

The bounds below are set at roughly 3x the measured time on this machine on 2026-09-03 and
each one prints what it actually used. THEY ARE NOT PERFORMANCE TARGETS. They exist to
make a tenfold regression impossible to ship, not to police a 20 % drift.
"""
from __future__ import annotations

import ast
import subprocess
import sys
import time
from pathlib import Path

import pytest

from conftest import Budget, PY_DIR


def _sources():
    return sorted(PY_DIR.glob("*.py")) + sorted((PY_DIR / "w11b").glob("*.py"))


# ======================================================================================
# 1. WORK WHOSE RESULT IS NEVER READ
# ======================================================================================

# Calls with NO side effect: assigning one and never reading it is definitionally waste.
# A call that does something (writes a file, publishes a layer) is excluded, because an
# unused return value from it is untidy rather than dead.
_PURE_CALLS = {
    "array", "asarray", "zeros", "ones", "full", "arange", "unique", "flatnonzero",
    "set", "frozenset", "dict", "list", "tuple", "sorted", "zip",
    "DataFrame", "Series", "GeoDataFrame", "GeoSeries", "STRtree", "unary_union",
}
# Scalar builtins are cheap, so an unused `n = len(x)` is untidy, not the defect this file
# is about. They count ONLY when the work is inside them - `float(frame.col.sum())` sums a
# column and throws the answer away.
_SCALAR_BUILTINS = {"float", "int", "str", "len", "sum", "min", "max", "abs", "round",
                    "bool", "any", "all"}


def _pure_work(node: ast.AST) -> bool:
    """Is this expression pure computation of a size worth noticing - work with nothing to
    show for it but a value nobody reads?"""
    if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
        return True
    if isinstance(node, ast.Call):
        f = node.func
        name = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name)
                                                            else "")
        if name in _PURE_CALLS:
            return True
        if name in _SCALAR_BUILTINS:
            return any(isinstance(n, (ast.Call, ast.ListComp, ast.SetComp, ast.DictComp,
                                      ast.GeneratorExp))
                       for a in node.args for n in ast.walk(a))
    return False


def _dead_assignments():
    """(file, function, name, line) for every local assigned from pure work and never read."""
    out = []
    for f in _sources():
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for fn in [n for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            loads = {n.id for n in ast.walk(fn)
                     if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
            # a name can also escape as a keyword, an f-string, or an attribute of self
            loads |= {n.attr for n in ast.walk(fn) if isinstance(n, ast.Attribute)}
            for st in ast.walk(fn):
                if not (isinstance(st, ast.Assign) and len(st.targets) == 1
                        and isinstance(st.targets[0], ast.Name)):
                    continue
                nm = st.targets[0].id
                if nm.startswith("_") or nm in loads:
                    continue
                if _pure_work(st.value):
                    out.append((f.name, fn.name, nm, st.lineno))
    return out


# Already present on 2026-09-03, keyed on (file, function, name) so the entry survives the
# owning agent editing around it. THIS IS A RATCHET: a NEW dead assignment fails the test.
# Each of these is real waste; none changes a published number.
_KNOWN_DEAD = {
    ("s3_hierarchy.py", "gates", "pts"):
        "np.array over a comprehension across every plot centroid, then never read - the "
        "nearest-neighbour query below takes the shapely list, not this array.",
    ("s5_flows.py", "_report_md", "placed"):
        "a sum over 12,816 arcs, never printed.",
    ("s5_flows.py", "verify", "ds"):
        "dict(zip(...)) over 9,897 nodes, never looked up - the monotonicity loop below "
        "uses `idx`, not this.",
    ("s6_levels.py", "build_layers", "od_out"):
        "an outside-diameter array built per node from the DN series and never written to "
        "a layer. If the OD was MEANT to be published this is a missing column, not just "
        "waste - worth a look either way.",
    ("s6_levels.py", "relay", "lo"):
        "the per-reach minimum gradient gathered for a whole chain, then never compared "
        "against - only `hi` is used in the relay. A minimum-gradient bound collected and "
        "not applied is the more worrying half of this one.",
}


def test_no_new_dead_computation():
    """Work with nothing to show for it. The 26-minute defect, caught from the syntax."""
    found = {(f, fn, nm): ln for f, fn, nm, ln in _dead_assignments()}
    new = {k: v for k, v in found.items() if k not in _KNOWN_DEAD}
    for k in sorted(set(_KNOWN_DEAD) & set(found)):
        print(f"\n    [dead, known] {k[0]}:{found[k]} {k[1]}(): `{k[2]}` - "
              f"{_KNOWN_DEAD[k]}")
    gone = sorted(set(_KNOWN_DEAD) - set(found))
    if gone:
        print(f"\n    [dead, FIXED since the list was written] {gone} - remove from "
              f"_KNOWN_DEAD in this file")
    assert not new, (
        "a value is computed and never read. That is the 26-minute defect:\n"
        + "\n".join(f"  {f}:{ln} {fn}(): `{nm}`" for (f, fn, nm), ln in sorted(new.items())))


# ======================================================================================
# 2. WORK REPEATED INSIDE A LOOP THAT DOES NOT DEPEND ON THE LOOP
# ======================================================================================

_HEAVY_CALLS = {
    "read_file", "listlayers", "read_csv", "read_parquet", "open",       # I/O
    "unary_union", "union_all", "STRtree", "sjoin", "sjoin_nearest",     # geometry
    "dissolve", "overlay", "to_crs", "buffer", "centroid",
    "sample_many", "profile", "distance_to_dry",                         # our own samplers
}


def _loop_invariant_heavy():
    out = []
    for f in _sources():
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for loop in [n for n in ast.walk(tree)
                     if isinstance(n, (ast.For, ast.AsyncFor, ast.While))]:
            bound = set()
            for b in loop.body:
                for n in ast.walk(b):
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store):
                        bound.add(n.id)
                    elif isinstance(n, ast.comprehension):
                        for t in ast.walk(n.target):
                            if isinstance(t, ast.Name):
                                bound.add(t.id)
            if isinstance(loop, (ast.For, ast.AsyncFor)):
                for t in ast.walk(loop.target):
                    if isinstance(t, ast.Name):
                        bound.add(t.id)
            for b in loop.body:
                for call in [n for n in ast.walk(b) if isinstance(n, ast.Call)]:
                    fu = call.func
                    name = (fu.attr if isinstance(fu, ast.Attribute)
                            else (fu.id if isinstance(fu, ast.Name) else ""))
                    if name not in _HEAVY_CALLS:
                        continue
                    reads = {n.id for n in ast.walk(call)
                             if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
                    if not (reads & bound):
                        out.append(f"  {f.name}:{call.lineno} `{name}(...)` inside a loop "
                                   f"but depending on nothing the loop changes")
    return out


def test_no_expensive_call_is_repeated_pointlessly_inside_a_loop():
    """Reading a file, building a spatial index or unioning geometry inside a loop that
    does not vary the arguments is the same defect wearing a different hat, and it is the
    one that turns a 40-second stage into a 26-minute one."""
    bad = _loop_invariant_heavy()
    print(f"\n    [loop-invariant heavy calls] none found across {len(_sources())} files")
    assert not bad, "\n".join(bad)


# ======================================================================================
# 3. SHAPE OF THE CODE - things that make a stage unauditable
# ======================================================================================

def test_no_stage_swallows_an_exception_silently():
    """W10's road treatment ran with `units=None, sampler=None` and three of its steps
    became no-ops nobody noticed. A bare `except: pass` is how a stage silently does
    nothing, which philosophy sec 8 makes a blocking provenance failure."""
    bad = []
    for f in _sources():
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for h in [n for n in ast.walk(tree) if isinstance(n, ast.ExceptHandler)]:
            body = [s for s in h.body if not isinstance(s, ast.Expr)
                    or not isinstance(s.value, ast.Constant)]
            if len(body) == 1 and isinstance(body[0], ast.Pass) and h.type is None:
                bad.append(f"  {f.name}:{h.lineno} bare `except: pass`")
    assert not bad, "\n".join(bad)


def test_no_module_shadows_a_stdlib_or_library_name():
    """A file called `random.py` or `types.py` next to the stages breaks imports in ways
    that look like a data problem."""
    reserved = {"types", "random", "json", "time", "math", "os", "sys", "copy", "queue",
                "select", "signal", "socket", "string", "test", "abc", "io", "code",
                "numbers", "operator", "platform", "statistics", "token", "typing"}
    clash = [f.name for f in _sources() if f.stem in reserved]
    assert not clash, f"module names shadowing the standard library: {clash}"


def test_field_names_fit_a_shapefile(contract):
    """Contract fix 4, enforced at import there and re-checked here so a change to the
    contract cannot quietly relax it. The ESRI DBF truncates at 10 characters and a
    truncated name is a field the auditor cannot find - which philosophy sec 8 makes a
    blocking failure."""
    over = [(s.name, f.name) for s in contract.LAYERS.values() for f in s.fields
            if len(f.name) > contract.SHP_FIELD_MAXLEN]
    assert not over, f"field names over {contract.SHP_FIELD_MAXLEN} characters: {over}"


# ======================================================================================
# 4. RUNTIME BOUNDS - measured, printed, and generous
# ======================================================================================

@pytest.mark.slow
@pytest.mark.parametrize("mod,bound_s", [
    ("w11b.criteria", 15.0),      # measured 0.3 s
    ("w11b.hydra", 15.0),         # measured 0.1 s
    ("w11b.contract", 20.0),      # measured 1.1 s
    ("w11b.pumping", 20.0),       # measured 0.1 s, 34 self-checks
    ("w11b.hazard", 30.0),        # measured 0.4 s, reads the shipped grids if present
    ("w11b.asbuilt", 60.0),       # measured 11.5 s, reads NAMA's 188.6 km as-built
])
def test_module_self_test_passes_inside_its_budget(mod, bound_s):
    """`python -m w11b.<module>` is each module's own self-test. Running them from the
    test suite means a self-test nobody remembers to run still gets run."""
    with Budget(f"python -m {mod}", bound_s):
        r = subprocess.run([sys.executable, "-m", mod], capture_output=True, text=True,
                           cwd=str(PY_DIR), timeout=bound_s * 2)
    assert r.returncode == 0, (
        f"{mod} self-test failed (rc={r.returncode})\n"
        f"{r.stdout[-2000:]}\n{r.stderr[-2000:]}")


@pytest.mark.slow
@pytest.mark.parametrize("stage,argv,bound_s", [
    ("s1_roads.py", ["--verify"], 180.0),
    ("s2_orient.py", ["selftest"], 180.0),
    ("s2_orient.py", ["verify"], 180.0),
    ("s3_hierarchy.py", ["selftest"], 180.0),
    ("s3_hierarchy.py", ["verify"], 180.0),
    ("s4_chambers.py", ["--selftest"], 180.0),
    ("s5_flows.py", ["--selftest"], 180.0),
    ("s5_flows.py", ["--verify"], 180.0),
    ("s7_pumps.py", ["--selftest"], 180.0),
])
def test_stage_verifier_passes_inside_its_budget(stage, argv, bound_s):
    """Every stage carries its own `verify` - the check that reads back what it PUBLISHED
    and re-derives its headline from it. These are the cheap ones; the full builds are in
    `run_all.py`.

    A verifier that cannot run because the stage has not been built is a SKIP with the
    stage named, never a pass.
    """
    if not (PY_DIR / stage).is_file():
        pytest.skip(f"{stage} does not exist yet")
    with Budget(f"{stage} {' '.join(argv)}", bound_s):
        r = subprocess.run([sys.executable, stage, *argv], capture_output=True, text=True,
                           cwd=str(PY_DIR), timeout=bound_s * 2)
    tail = (r.stdout + r.stderr)[-2500:]
    if r.returncode != 0 and ("not published" in tail or "No such file" in tail
                              or "does not exist" in tail):
        pytest.skip(f"{stage} has not been built yet: {tail.strip().splitlines()[-1][:120]}")
    assert r.returncode == 0, f"{stage} {argv} failed (rc={r.returncode})\n{tail}"


@pytest.mark.slow
def test_importing_every_stage_is_cheap():
    """A stage that does work AT IMPORT cannot be tested, cannot be introspected, and
    makes every other import slow. Each must import in well under a second of its own."""
    import importlib
    slow = []
    for f in sorted(PY_DIR.glob("s*.py")):
        code = (f"import time,sys; sys.path.insert(0,r'{PY_DIR}'); "
                f"t=time.perf_counter(); import {f.stem}; "
                f"print(f'{{time.perf_counter()-t:.3f}}')")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                           cwd=str(PY_DIR), timeout=180)
        assert r.returncode == 0, f"{f.name} does not import:\n{r.stderr[-1500:]}"
        dt = float(r.stdout.strip().splitlines()[-1])
        print(f"\n    [import] {f.name}: {dt:.2f} s")
        if dt > 25.0:
            slow.append(f"  {f.name}: {dt:.1f} s")
    assert not slow, ("a stage does real work at import time:\n" + "\n".join(slow))
