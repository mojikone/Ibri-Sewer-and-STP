#!/usr/bin/env python
"""W12 - run the whole pipeline from a cold start, then audit what it produced.

    python run_all.py                 preflight, build every stage in order, verify each,
                                      run the test gate, then run the auditor
    python run_all.py --list          print the plan and what is runnable, change nothing
    python run_all.py --verify-only   no builds: verify + gate + audit what is published
    python run_all.py --audit-only    just the auditor, against the published layers
    python run_all.py --from s4       resume at a stage (and run everything after it)
    python run_all.py --only s5       one stage, its verifier, and stop
    python run_all.py --no-audit      stop after the test gate
    python run_all.py --keep-going    do not stop at the first failure: record it and go on,
                                      so the auditor still runs. The DEFAULT is to stop.
    python run_all.py -k slow         extra -k / -m arguments handed to the test gate

WHAT IT DOES, IN THE ORDER PHILOSOPHY sec 2 PUTS IT

    0  PREFLIGHT      python, the libraries, the input files, the terrain products, and
                      every module's own self-test. Nothing builds until these pass,
                      because a stage that fails on a missing input 40 minutes in has
                      wasted 40 minutes.
    1..8  THE STAGES  in numeric order, which is the order of design. Each is built with
                      no arguments and then re-verified against WHAT IT WROTE, never
                      against what it held in memory.
    9  THE GATE       `pytest tests -m "not audit"` - the correctness tests. A failure
                      here is a code defect and it stops the run.
    10 THE AUDITOR    `pytest tests -m audit` - the philosophy's hard constraints, checked
                      against the PUBLISHED layers. A failure here is an engineering
                      finding, printed as a table, and it sets the exit code without
                      pretending the build broke.

    IT STOPS AT THE FIRST FAILURE and prints what failed, what it was doing, and what to
    run to see more. A stage that does not exist yet, or exists without a CLI, is reported
    as NOT RUNNABLE rather than skipped in silence - philosophy sec 8: a check that cannot
    run is a failure, not a blank.

EXIT CODES
    0   everything ran and everything passed
    1   preflight, a stage, a verifier or the test gate failed
    2   all of that passed and the AUDITOR found a breach of a hard constraint
    3   a stage in the design order could not be run at all

WHAT THIS FILE DOES NOT DO. It does not import a stage - every one is run as its own
process, so a stage that leaves global state, holds a raster open or exits hard cannot
take the runner with it, and the wall-clock time it prints is the real one.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

PY_DIR = Path(__file__).resolve().parent          # .../W12/py
W12 = PY_DIR.parent                              # .../W12
CLAUDE = W12.parent                              # .../Hydraulic/Claude
HYDRAULIC = CLAUDE.parent                         # .../Hydraulic
TESTS = PY_DIR / "tests"

if str(PY_DIR) not in sys.path:
    sys.path.insert(0, str(PY_DIR))


# ======================================================================================
# THE PLAN
# ======================================================================================

@dataclass
class Stage:
    """One stage of the design order (philosophy sec 2)."""
    n: int
    file: str
    what: str                       # what it decides, in the philosophy's words
    publishes: Tuple[str, ...] = ()  # the GeoPackage(s) under W12/shp it must produce
    build_argv: Tuple[str, ...] = ()
    bound_s: float = 1800.0         # a wall-clock ceiling, ~10x the measured time
    optional: bool = False          # not yet part of the numbered design order

    @property
    def path(self) -> Path:
        return PY_DIR / self.file

    @property
    def exists(self) -> bool:
        return self.path.is_file()

    @property
    def runnable(self) -> bool:
        """A stage is runnable when it exists AND exposes a `main`. A half-written stage
        that imports cleanly but has no entry point is NOT runnable, and saying so is the
        point: it is a stage of the design order that cannot be executed."""
        if not self.exists:
            return False
        return re.search(r"^def main\(", self.path.read_text(encoding="utf-8"), re.M) is not None

    @property
    def verify_argv(self) -> Optional[Tuple[str, ...]]:
        """The two conventions in this folder, detected from the source rather than
        guessed: an argparse `--verify` flag, or a positional `verify` command."""
        if not self.exists:
            return None
        src = self.path.read_text(encoding="utf-8")
        if '"--verify"' in src:
            return ("--verify",)
        if 'cmd == "verify"' in src or '"verify"' in src:
            return ("verify",)
        return None


# Every stage in this folder builds with NO arguments: the argparse stages default to a
# build, and the positional stages read `cmd = argv[0] if argv else "build"`.
# Bounds are ~10x the time measured on 2026-09-03 and exist to stop a hung run, not to
# police performance - the per-stage timings live in tests/test_deadcode.py.
STAGES: List[Stage] = [
    Stage(1, "s1_roads.py", "the corridors - what a pipe may run along",
          ("W12_roads.gpkg",), bound_s=2400),
    Stage(2, "s2_orient.py", "which way the ground drains, and the oriented arcs",
          ("W12_orient.gpkg",), bound_s=1800),
    Stage(3, "s3_hierarchy.py", "the hierarchy - one pipe leaves every junction",
          ("W12_hier.gpkg",), bound_s=1800),
    Stage(4, "s4_chambers.py", "the chambers, and the tertiary connections",
          ("W12_chambers.gpkg",), bound_s=1800),
    Stage(5, "s5_flows.py", "flow accumulation and peaking",
          ("W12_flows.gpkg",), bound_s=900),
    Stage(6, "s6_levels.py", "levels and sizes - the part software does", (), bound_s=3600),
    Stage(7, "s7_pumps.py", "the lifting stations and their rising mains",
          ("W12_pumps.gpkg",), bound_s=1800),
    Stage(8, "s8_export.py", "the export - shapefiles, DXF, schedules, model", (),
          bound_s=3600),
]

# Prerequisites that are NOT stages: they are built once and cost hours, so the runner
# checks them and names the command rather than rebuilding them behind your back.
PREREQ_FILES: List[Tuple[str, Path, str]] = [
    ("the cleaned road DXF",
     HYDRAULIC / "DWG" / "road network 03092026 eyeballed.dxf",
     "the engineer's cleaned DXF of 03/09/2026 - stage 1's only road input"),
    ("the study boundary DXF",
     HYDRAULIC / "DWG" / "Project Boundary.dxf",
     "a separate drawing; the road DXF carries no boundary polygon"),
    ("the plot loads",
     CLAUDE / "W10" / "shp" / "W10_plot_loads.gpkg",
     "read for DATA by stages 1, 3 and 5. Copying data across iterations is fine; "
     "importing code is not"),
    ("the terrain VRT",
     HYDRAULIC.parent / "Data" / "Terrain" / "Sat_0p5m" / "IBRI_0p5_VRT2.vrt",
     "project rule 6: the 0.5 m bare-earth blend, EPSG:32640"),
]

PREREQ_DERIVED: List[Tuple[str, Path, str]] = [
    ("the R5 flow-direction grid", W12 / "run" / "terrain" / "R5_d8.tif",
     "python -m w12.terrain build --grid R5   (hours, ~25 GB - do not rebuild casually)"),
    ("the R5 accumulation grid", W12 / "run" / "terrain" / "R5_acc.tif",
     "python -m w12.terrain build --grid R5"),
    ("the stream network", W12 / "shp" / "W12_streams.gpkg",
     "python -m w12.streams   (about 85 s)"),
]

MODULE_SELFTESTS: List[Tuple[str, float]] = [
    ("w12.criteria", 60), ("w12.hydra", 60), ("w12.contract", 120),
    ("w12.pumping", 120), ("w12.hazard", 180), ("w12.asbuilt", 300),
]


# ======================================================================================
# running things
# ======================================================================================

@dataclass
class Result:
    step: str
    ok: bool
    seconds: float = 0.0
    note: str = ""
    tail: str = ""
    full: str = ""
    skipped: bool = False


RESULTS: List[Result] = []
T0 = time.time()
KEEP_GOING = False
FAILURES: List[str] = []


def _c(s: str, code: str) -> str:
    if os.environ.get("NO_COLOR") or not sys.stdout.isatty():
        return s
    return f"\033[{code}m{s}\033[0m"


def say(msg: str = "") -> None:
    print(msg, flush=True)


def head(msg: str) -> None:
    say()
    say(_c("=" * 86, "90"))
    say(_c(f"  {msg}", "1"))
    say(_c("=" * 86, "90"))


def run(step: str, argv: Sequence[str], *, bound_s: float, cwd: Path = PY_DIR,
        note: str = "") -> Result:
    """Run one command as its own process, print its tail, and time it."""
    say(f"\n  -> {step}")
    say(f"     {' '.join(str(a) for a in argv)}")
    t = time.perf_counter()
    try:
        p = subprocess.run([str(a) for a in argv], cwd=str(cwd), text=True,
                           capture_output=True, timeout=bound_s)
        rc, out = p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired as e:
        rc = -9
        out = (e.stdout or "") + (e.stderr or "") if isinstance(e.stdout, str) else ""
        out += f"\n*** TIMED OUT after {bound_s:.0f} s ***"
    dt = time.perf_counter() - t
    tail = "\n".join(out.strip().splitlines()[-25:])
    ok = rc == 0
    say(f"     {_c('OK ' if ok else 'FAIL', '32' if ok else '31')}  {dt:,.1f} s"
        + (f"   {note}" if note else ""))
    if tail:
        for ln in tail.splitlines()[-(6 if ok else 25):]:
            say(f"       | {ln}")
    r = Result(step, ok, dt, note, tail, out)
    RESULTS.append(r)
    return r


def skip(step: str, note: str) -> Result:
    say(f"\n  -> {step}")
    say(f"     {_c('SKIP', '33')}  {note}")
    r = Result(step, True, 0.0, note, skipped=True)
    RESULTS.append(r)
    return r


def die(msg: str, code: int = 1) -> None:
    """Stop at the first failure - the default, and the point of the runner.

    `--keep-going` records the failure and continues, which is the mode to use when a
    stage another agent owns is red and you still need the auditor's table. It never
    turns a failure into a pass: the exit code and the summary carry it either way.
    """
    say()
    say(_c("-" * 86, "31"))
    say(_c(f"  {'FAILED' if KEEP_GOING else 'STOPPED'}: {msg}", "1;31"))
    say(_c("-" * 86, "31"))
    FAILURES.append(msg.splitlines()[0])
    if KEEP_GOING:
        return
    summary()
    raise SystemExit(code)


# ======================================================================================
# 0. PREFLIGHT
# ======================================================================================

def preflight(strict_inputs: bool = True) -> None:
    head("0  PREFLIGHT - nothing builds until these pass")

    if sys.version_info < (3, 10):
        die(f"python {sys.version.split()[0]} is too old; the stages use 3.10+ syntax")
    say(f"\n  python {sys.version.split()[0]}  at  {sys.executable}")

    missing = []
    versions = []
    for mod in ("numpy", "pandas", "geopandas", "shapely", "rasterio", "fiona",
                "networkx", "pyproj", "scipy", "pytest"):
        try:
            m = __import__(mod)
            versions.append(f"{mod} {getattr(m, '__version__', '?')}")
        except Exception as e:                                      # noqa: BLE001
            missing.append(f"{mod} ({e})")
    say("  " + " | ".join(versions))
    if missing:
        die("missing python packages: " + ", ".join(missing)
            + "\n  Fix: run _SETUP/bootstrap.ps1 from the repo root.")
    RESULTS.append(Result("preflight: python and libraries", True))

    say("\n  INPUT DATA (client files and earlier-iteration DATA - never code)")
    bad = []
    for name, p, why in PREREQ_FILES:
        ok = p.exists()
        say(f"    {_c('found  ' if ok else 'MISSING', '32' if ok else '31')}  "
            f"{name:26s}  {p}")
        if not ok:
            bad.append(f"    {name}: {p}\n      {why}")
    if bad and strict_inputs:
        die("input data missing:\n" + "\n".join(bad))
    RESULTS.append(Result("preflight: input data", not bad))

    say("\n  DERIVED PREREQUISITES (built once, hours - the runner never rebuilds these)")
    bad = []
    for name, p, how in PREREQ_DERIVED:
        ok = p.exists()
        say(f"    {_c('found  ' if ok else 'MISSING', '32' if ok else '31')}  "
            f"{name:26s}  {p.name}")
        if not ok:
            bad.append(f"    {name}\n      build it with:  {how}")
    if bad:
        die("terrain or stream products missing:\n" + "\n".join(bad)
            + "\n\n  These are inputs to stage 2 onwards. They are deliberately NOT part\n"
              "  of this runner: rebuilding the terrain is hours of work and 25 GB, and\n"
              "  doing it silently inside a pipeline run is how a morning disappears.")
    RESULTS.append(Result("preflight: terrain and streams", True))

    head("0b  MODULE SELF-TESTS - the engineering library checks itself")
    for mod, bound in MODULE_SELFTESTS:
        r = run(f"self-test {mod}", [sys.executable, "-m", mod], bound_s=bound)
        if not r.ok:
            die(f"{mod} fails its own self-test. Nothing downstream may design anything "
                f"on a library that does not agree with the guideline.\n"
                f"  See it in full:  python -m {mod}")


# ======================================================================================
# 1..8  THE STAGES
# ======================================================================================

def plan(from_n: int = 0, only_n: Optional[int] = None) -> List[Stage]:
    return [s for s in STAGES
            if (only_n is None and s.n >= from_n) or (only_n is not None and s.n == only_n)]


def show_plan() -> int:
    head("THE PLAN - philosophy sec 2, the order of design")
    say(f"\n  {'#':>2}  {'stage':16s} {'status':14s} {'verify':9s}  decides")
    say("  " + "-" * 84)
    cannot = 0
    for s in STAGES:
        if not s.exists:
            st, col = "not written", "33"
            cannot += 1
        elif not s.runnable:
            st, col = "NO CLI", "31"
            cannot += 1
        else:
            st, col = "runnable", "32"
        v = " ".join(s.verify_argv) if s.verify_argv else _c("none", "33")
        say(f"  {s.n:>2}  {s.file:16s} {_c(st, col):23s} {v:9s}  {s.what}")
    say("\n  Published GeoPackages expected under W12/shp:")
    for s in STAGES:
        for g in s.publishes:
            p = W12 / "shp" / g
            say(f"    {_c('present' if p.exists() else 'absent ', '32' if p.exists() else '33')}"
                f"  {g}")
    if cannot:
        say(f"\n  {_c(f'{cannot} stage(s) of the design order cannot be run.', '33')} "
            f"Philosophy sec 8 counts that as a failure, not a blank.")
    return 3 if cannot else 0


def build_stages(stages: Sequence[Stage], verify_only: bool) -> int:
    not_runnable = []
    for s in stages:
        head(f"{s.n}  {s.file} - {s.what}")

        if not s.exists:
            skip(f"stage {s.n} build", f"{s.file} has not been written yet")
            not_runnable.append(f"  stage {s.n} ({s.what}): {s.file} does not exist")
            continue
        if not s.runnable:
            skip(f"stage {s.n} build", f"{s.file} exists but exposes no main()")
            not_runnable.append(f"  stage {s.n} ({s.what}): {s.file} has no CLI entry point")
            continue

        if verify_only:
            skip(f"stage {s.n} build", "--verify-only")
        else:
            r = run(f"stage {s.n} build", [sys.executable, s.file, *s.build_argv],
                    bound_s=s.bound_s)
            if not r.ok:
                die(f"stage {s.n} ({s.file}) failed to build.\n"
                    f"  Reproduce:  cd {PY_DIR} && python {s.file}\n"
                    f"  Everything after it is now unrunnable, so the run stops here.")

        for g in s.publishes:
            p = W12 / "shp" / g
            if not p.exists():
                die(f"stage {s.n} finished without publishing {g}.\n"
                    f"  Expected:  {p}\n"
                    f"  A stage that returns 0 and writes nothing is a stage silently "
                    f"doing nothing (philosophy sec 8, provenance check 3).")
            RESULTS.append(Result(f"stage {s.n} published {g}", True, 0.0,
                                  f"{p.stat().st_size / 1e6:,.1f} MB"))

        va = s.verify_argv
        if va is None:
            skip(f"stage {s.n} verify", f"{s.file} exposes no verifier")
            not_runnable.append(f"  stage {s.n}: no verifier - nothing re-reads what it wrote")
        else:
            r = run(f"stage {s.n} verify", [sys.executable, s.file, *va], bound_s=s.bound_s)
            if not r.ok:
                # Distinguish "this stage has never been built" from "this stage disagrees
                # with what it wrote". Both are failures; only the second is a defect, and
                # reporting them as the same thing hides the one that matters.
                never_built = any(t in r.full for t in (
                    "could not be opened", "No such file", "does not exist",
                    "not published", "FileNotFoundError", "DataLayerError",
                    "DataSourceError"))
                if never_built and verify_only:
                    RESULTS[-1] = Result(f"stage {s.n} verify", True, r.seconds,
                                         "never built - its verifier has nothing to read",
                                         r.tail, r.full, skipped=True)
                    say(_c("     -> reclassified: this stage has never been built, so its "
                           "verifier has nothing to read. Run it without --verify-only.",
                           "33"))
                    not_runnable.append(
                        f"  stage {s.n} ({s.what}): never built, so its verifier cannot run")
                    continue
                die(f"stage {s.n} verified its OWN PUBLISHED OUTPUT and disagreed with it.\n"
                    f"  Reproduce:  cd {PY_DIR} && python {s.file} {' '.join(va)}")

    if not_runnable:
        say()
        say(_c("  STAGES OF THE DESIGN ORDER THAT COULD NOT BE RUN:", "33"))
        for line in not_runnable:
            say(_c(line, "33"))
    return 3 if not_runnable else 0


# ======================================================================================
# 9 and 10  THE GATE AND THE AUDITOR
# ======================================================================================

def pytest_argv(marker: str, extra: Sequence[str]) -> List[str]:
    return [sys.executable, "-m", "pytest", str(TESTS), "-q", "-s",
            "-m", marker, "--no-header", "-p", "no:cacheprovider", *extra]


def gate(extra: Sequence[str]) -> None:
    head("9  THE GATE - the correctness tests. A failure here is a code defect.")
    r = run("pytest -m 'not audit'", pytest_argv("not audit", extra), bound_s=3600)
    if not r.ok:
        die("the test gate failed. These are tests of the CODE, not of the design:\n"
            "  the physics, the constants, the no-data rule, the published columns and\n"
            "  the graph invariants.\n"
            f"  Reproduce:  cd {PY_DIR} && python -m pytest tests -m 'not audit'")


def audit(extra: Sequence[str]) -> int:
    head("10  THE AUDITOR - the philosophy's hard constraints, against the PUBLISHED layers")
    say("\n  W12 has no separate auditor module. These checks ARE the auditor: each one\n"
        "  names the rule it enforces (H1-H16) and the guideline page behind it, and each\n"
        "  reads a published GeoPackage rather than an in-memory model. Philosophy sec 8:\n"
        "  a breach of a 'shall' is BLOCKING, and a check that cannot run is a failure.")
    r = run("pytest -m audit", pytest_argv("audit", extra), bound_s=3600)

    # The value of the audit is not the pass/fail - it is the MEASURED NUMBER each check
    # printed. Pull those out of the captured output and print them as the audit table,
    # because a check that reports "PASS" and nothing else cannot be argued with.
    # `    [tag] words...` is the suite's own convention for a measured line. The
    # exclusion is pandas' `[12816 rows x 30 columns]` repr, which looks identical.
    measured = [ln.rstrip() for ln in r.full.splitlines()
                if re.match(r"\s+\[[a-zA-Z][^\]]*\]\s+\S", ln)]
    if measured:
        say()
        say(_c("  WHAT THE AUDIT MEASURED", "1"))
        for ln in measured:
            say(f"    {ln.strip()}")

    if r.ok:
        say(_c("\n  AUDIT: every check passed.", "32"))
        return 0
    fails = [ln for ln in r.full.splitlines() if ln.startswith("FAILED")]
    if not fails:
        # The auditor did not run at all - a collection error, a crash, a timeout. Under
        # philosophy sec 8 that is the WORST outcome, not the cleanest: a check that
        # cannot run is a failure, not a blank.
        say()
        say(_c("  AUDIT DID NOT RUN. This is a failure, not a clean sheet - philosophy "
               "sec 8.", "1;31"))
        say(_c(f"    {r.tail.splitlines()[-1] if r.tail else 'no output'}", "31"))
        return 2
    say()
    say(_c(f"  AUDIT: {len(fails)} check(s) failed. These are ENGINEERING FINDINGS, not a "
           f"broken build.", "33"))
    for ln in fails:
        say(_c(f"    {ln}", "33"))
    say(f"\n  See each one in full:  cd {PY_DIR} && python -m pytest tests -m audit -s")
    return 2


# ======================================================================================
# summary
# ======================================================================================

def summary() -> None:
    head("SUMMARY")
    w = max((len(r.step) for r in RESULTS), default=10)
    say()
    for r in RESULTS:
        state = ("SKIP" if r.skipped else ("OK" if r.ok else "FAIL"))
        col = "33" if r.skipped else ("32" if r.ok else "31")
        t = f"{r.seconds:8,.1f} s" if r.seconds else " " * 10
        say(f"  {_c(state.ljust(4), col)}  {r.step.ljust(w)}  {t}  {r.note}")
    n_ok = sum(1 for r in RESULTS if r.ok and not r.skipped)
    n_skip = sum(1 for r in RESULTS if r.skipped)
    n_bad = sum(1 for r in RESULTS if not r.ok)
    say(f"\n  {n_ok} passed, {n_skip} skipped, {n_bad} failed in "
        f"{time.time() - T0:,.1f} s wall clock")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__.splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="\n".join(__doc__.splitlines()[1:]))
    ap.add_argument("--list", action="store_true", help="print the plan and exit")
    ap.add_argument("--verify-only", action="store_true",
                    help="do not build; verify, gate and audit what is already published")
    ap.add_argument("--audit-only", action="store_true", help="just the auditor")
    ap.add_argument("--no-audit", action="store_true", help="stop after the test gate")
    ap.add_argument("--no-gate", action="store_true", help="skip the correctness tests")
    ap.add_argument("--from", dest="from_stage", default=None, metavar="sN",
                    help="resume at this stage, e.g. --from s4")
    ap.add_argument("--only", default=None, metavar="sN", help="run one stage and stop")
    ap.add_argument("--keep-going", action="store_true",
                    help="record a failure and carry on, so the auditor still runs")
    ap.add_argument("--skip-preflight", action="store_true")
    ap.add_argument("-k", "--pytest-arg", action="append", default=[], dest="pytest_extra",
                    help="extra argument passed through to pytest (repeatable)")
    a = ap.parse_args(argv)

    def _n(v):
        if v is None:
            return None
        m = re.search(r"\d+", str(v))
        if not m:
            ap.error(f"cannot read a stage number from {v!r}")
        return int(m.group())

    global KEEP_GOING
    KEEP_GOING = bool(a.keep_going)

    if a.list:
        return show_plan()

    say(_c("W12 - full pipeline run", "1"))
    say(f"  py      {PY_DIR}")
    say(f"  shp     {W12 / 'shp'}")
    say(f"  started {time.strftime('%Y-%m-%d %H:%M:%S')}")

    rc = 0
    if a.audit_only:
        return audit(a.pytest_extra)

    if not a.skip_preflight:
        preflight()

    rc = max(rc, build_stages(plan(_n(a.from_stage) or 0, _n(a.only)), a.verify_only))

    if a.only is None:
        if not a.no_gate:
            gate(a.pytest_extra)
        if not a.no_audit:
            rc = max(rc, audit(a.pytest_extra))

    summary()
    if FAILURES:
        say(_c(f"\n  {len(FAILURES)} FAILURE(S), carried past because --keep-going:",
               "1;31"))
        for f in FAILURES:
            say(_c(f"    {f}", "31"))
        say(_c("\n  THE RUN DID NOT PASS. --keep-going carried past the failures above so "
               "the auditor\n  could still run; it did not make them go away. Nothing from "
               "this run is quotable\n  until they are fixed.\n", "1;31"))
        return max(rc, 1)
    if rc == 0:
        say(_c("\n  ALL GREEN.\n", "1;32"))
    elif rc == 2:
        say(_c("\n  BUILD AND GATE PASSED; THE AUDIT FOUND BREACHES OF HARD CONSTRAINTS.\n",
               "1;33"))
    elif rc == 3:
        say(_c("\n  STAGES OF THE DESIGN ORDER COULD NOT BE RUN - see the list above.\n",
               "1;33"))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
