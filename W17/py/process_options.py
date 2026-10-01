"""Follow the seven-option build in the VM and process each option as soon as its last run is exported.

    python -u process_options.py S2 S3 S4 S5 S6 S7
For each option: wait for outfalls_S#-2060.csv (the build's last export of an option), check that the 2070 analysis and
every year kept the 2070 design (sizes and inverts), then run scenario_results.py and make_option_layers.py.
One line per event on stdout, so a monitor can follow it; a failure prints FAILED and the error, and moves on.
"""
import csv, os, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
SCEN = r"D:\VBOX\bridge\out\scen"
GIS = os.path.join(os.path.dirname(HERE), "gis")
TAGS = ["2070a", "2030", "2040", "2050", "2055", "2060"]


def stable(path, wait=20):
    """The file exists and has not grown for `wait` seconds."""
    if not os.path.exists(path):
        return False
    a = os.path.getsize(path); time.sleep(wait)
    return os.path.exists(path) and os.path.getsize(path) == a


def design_kept(o):
    rd = lambda tag: {r["label"]: (r["size_label"], r["start_inv"], r["stop_inv"])
                      for r in csv.DictReader(open(os.path.join(SCEN, o, f"conduits_{o}-{tag}.csv"), encoding="utf-8"))}
    des = rd("2070")
    return {t: sum(1 for l, v in rd(t).items() if des.get(l) != v) for t in TAGS}


def run(args, cwd):
    p = subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, p.stdout, p.stderr


for o in sys.argv[1:]:
    last = os.path.join(SCEN, o, f"outfalls_{o}-2060.csv")
    while not stable(last):
        time.sleep(30)
    try:
        diff = design_kept(o)
        bad = {t: n for t, n in diff.items() if n}
        print(f"{o}: exports complete; runs differing from the 2070 design: {bad or 'none'}"
              + ("  FAILED guard" if bad else ""), flush=True)
        rc, out, err = run(["scenario_results.py", o], HERE)
        if rc:
            print(f"{o}: scenario_results FAILED\n{err[-800:]}", flush=True); continue
        lines = [l for l in out.splitlines() if l.startswith(("| " + o + "-", "Total:", "Manholes deeper", "Design 2070", "Flow check"))]
        print(f"{o}: results\n  " + "\n  ".join(lines), flush=True)
        rc, out, err = run(["make_option_layers.py", o], GIS)
        print(f"{o}: layers " + ("FAILED\n" + err[-800:] if rc else out.strip().splitlines()[-1]), flush=True)
    except Exception as e:  # noqa: BLE001
        print(f"{o}: FAILED {type(e).__name__}: {e}", flush=True)
print("all options processed", flush=True)
