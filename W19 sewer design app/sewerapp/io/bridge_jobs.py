"""Export any SewerGEMS model for the app through the VM bridge (clean room: SewerGEMS's own documented API does the
reading, inside the offline VM; the app never reads a SewerGEMS file).

The VM's watcher runs every `bridge/jobs/*.ps1` in name order, writes `bridge/out/<job>.txt` ending `__EXIT__ <code>`,
then moves the job to `bridge/done/`; it rewrites `bridge/out/_alive.txt` every 2 s while idle. This module lists the
models in the shared folders, writes one job per export (the model is COPIED inside the guest and only the copy is
opened: nothing is written beside the modeller's file), and reports a job's state. The export lands in
`bridge/out/w19/export/<tag>/`; `scenarios.csv` is written last, so a folder without it is not finished."""
import datetime as dt, os, re, time

BRIDGE = os.environ.get("W19_BRIDGE", r"D:\VBOX\bridge")
EXPORTS = os.environ.get("W19_SG_EXPORTS", os.path.join(BRIDGE, "out", "w19", "export"))
# host folder -> the same folder as the guest sees it (VirtualBox shared folders)
SHARES = [(os.path.join(os.path.expanduser("~"), "Desktop", "Win10 shared folder"), r"\\VBOXSVR\Win10_shared_folder"),
          (os.path.join(BRIDGE, "models"), r"\\VBOXSVR\VBOX\bridge\models")]
if "W19_MODEL_SHARES" in os.environ:                       # "host folder=guest folder;..." (tests point it at temporary folders)
    SHARES = [tuple(x.split("=", 1)) for x in os.environ["W19_MODEL_SHARES"].split(";") if "=" in x]
SKIP = re.compile(r"(system volume information|\$recycle|installer|licens|crack|\.zip$)", re.I)

TEMPLATE = r"""# W19: export a SewerGEMS model for the app (this job was written by the app). Every scenario: the elements, their
# attributes, the results the model holds, the loads and the peaking support. The model is COPIED first and only the
# copy is opened, so nothing is written beside the modeller's file. scenarios.csv is written last. With $run, every
# scenario is computed first on the copy (a model saved without results then has them; a storm model takes minutes each).
# Boxes and open channels also get sections_<file>.csv (Sections.cs: shape, dimensions, n and their results in SI).
$src = '__SRC__'
$tag = '__TAG__'
$run = $__RUN__
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\export\$tag"; New-Item -ItemType Directory -Force $out | Out-Null
$dir = "C:\IbriWork\W19\src\$tag"; New-Item -ItemType Directory -Force $dir | Out-Null
Remove-Item -LiteralPath "$out\scenarios.csv", "$out\log.txt" -ErrorAction SilentlyContinue
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
if (Test-Path -LiteralPath "$src.sqlite") { Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force }
$work = "$dir\work.stsw"
$log = New-Object IO.StringWriter
$log.WriteLine(("source {0}" -f $src))
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $m.SaveAs($work)
  $sm = $m.DomainDataSet.ScenarioManager
  $rows = @('id,label,parent,file')
  [Geometry]::Export($m, "$out\geometry.tsv", $log)
  [LoadsDump]::SupportLoads($m, "$out\support_loads.csv", $log)
  $k = 0
  foreach ($s in $sm.Elements()) {
    $k += 1; $file = 's{0:000}' -f $k
    $rows += ('{0},"{1}",{2},{3}' -f $s.Id, ($s.Label -replace '"', "'"), $s.ParentID, $file)
    $m.SetActiveScenario($m.Scenarios.Element($s.Id))
    if ($run) {
      $ct = ''; try { $ct = [string]$m.Scenarios.Element($s.Id).Options.GvfCalculationType } catch {}
      if ($ct -eq 'Design') { $log.WriteLine("  calculation type Design: SewerGEMS's run re-sizes the conduits of the copy, as its Compute would") }
      [Scen]::Run($m, $s.Id, $log)
    }
    [Scen]::Export($m, $out, $file, $log)
    try { [Sections]::Export($m, "$out\sections_$file.csv", $log) } catch { $log.WriteLine("  sections not exported: " + $_.Exception.Message) }
    [LoadsDump]::ScenarioLoads($m, $s.Id, "$out\loads_$file.csv", $log)
    $log.WriteLine(("  scenario {0} '{1}' -> {2}" -f $s.Id, $s.Label, $file))
    [IO.File]::WriteAllText("$out\log.txt", $log.ToString())       # progress, read by the app while the job runs
  }
  $m.Close()
  [IO.File]::WriteAllLines("$out\scenarios.csv", $rows)
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
"""


def tag_of(name):
    t = re.sub(r"[^A-Za-z0-9_-]+", "_", os.path.splitext(os.path.basename(name))[0]).strip("_")
    return t[:60] or "model"


def guest_path(host):
    h = os.path.normcase(os.path.abspath(host))
    for root, guest in SHARES:
        r = os.path.normcase(os.path.abspath(root))
        if h == r or h.startswith(r + os.sep): return guest + os.path.abspath(host)[len(r):].replace("/", "\\")   # the name's own case
    return None


def watcher():
    """Whether the VM's watcher is up: its heartbeat is at most 30 s old, or it is busy with a job."""
    f = os.path.join(BRIDGE, "out", "_alive.txt")
    if not os.path.exists(f): return dict(alive=False, reason="the bridge has never run (no heartbeat file)")
    age = time.time() - os.path.getmtime(f)                 # the host's clock: the VM's clock runs some seconds apart
    busy = [j for j in jobs() if j["state"] == "running"]
    return dict(alive=age < 30 or bool(busy), age_s=round(age), busy=bool(busy),
                reason=None if age < 30 or busy else "start bridge\\watcher.ps1 in a PowerShell window inside the VM")


def models():
    """SewerGEMS models (.stsw) in the shared folders, newest first."""
    out = []
    for root, _ in SHARES:
        if not os.path.isdir(root): continue
        base = root.rstrip("\\/").count(os.sep)
        for d, dirs, files in os.walk(root):
            dirs[:] = [x for x in dirs if not SKIP.search(x)]
            if d.count(os.sep) - base >= 4: dirs[:] = []
            for f in files:
                if f.lower().endswith(".stsw"):
                    p = os.path.join(d, f)
                    out.append(dict(name=f, folder=os.path.relpath(d, root), host=p, guest=guest_path(p), tag=tag_of(f),
                                    mb=round(os.path.getsize(p + ".sqlite") / 1e6, 1) if os.path.exists(p + ".sqlite") else None,
                                    modified=dt.datetime.fromtimestamp(os.path.getmtime(p)).strftime("%Y-%m-%d %H:%M"),
                                    exported=os.path.exists(os.path.join(EXPORTS, tag_of(f), "scenarios.csv"))))
    return sorted(out, key=lambda m: m["modified"], reverse=True)


def submit(guest, tag, run=False):
    if not re.match(r"^(\\\\VBOXSVR\\|[A-Za-z]:\\)", guest or ""): raise ValueError("give the model's path as the VM sees it (C:\\... or \\\\VBOXSVR\\...)")
    if not guest.lower().endswith(".stsw"): raise ValueError("a SewerGEMS model is a .stsw file")
    tag = tag_of(tag or guest)
    name = f"w19x_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{tag}.ps1"
    os.makedirs(os.path.join(BRIDGE, "jobs"), exist_ok=True)
    body = TEMPLATE.replace("__SRC__", guest.replace("'", "''")).replace("__TAG__", tag).replace("__RUN__", "true" if run else "false")
    with open(os.path.join(BRIDGE, "jobs", name), "w", encoding="utf-8") as f: f.write(body)
    return dict(job=name[:-4], tag=tag)


def job(name):
    """queued (in jobs/), running (in jobs/ with output started), done or failed (its output ends __EXIT__)."""
    jf, of = os.path.join(BRIDGE, "jobs", name + ".ps1"), os.path.join(BRIDGE, "out", name + ".txt")
    tag = name.split("_", 3)[3] if name.count("_") >= 3 else None
    state, code = "unknown", None
    # the job's own output is UTF-16 (PowerShell's redirection) and the watcher appends __EXIT__ in the console encoding:
    # dropping the zero bytes reads both
    txt = open(of, "rb").read().replace(b"\x00", b"").decode("latin-1", errors="ignore") if os.path.exists(of) else ""
    m = re.search(r"__EXIT__\s+(-?\d+)", txt)
    if m: code = int(m.group(1)); state = "done" if code == 0 else "failed"
    elif os.path.exists(jf): state = "running" if os.path.exists(of) else "queued"
    elif os.path.exists(os.path.join(BRIDGE, "done", name + ".ps1")): state = "done"
    exp = os.path.join(EXPORTS, tag) if tag else None
    log = ""
    if exp and os.path.exists(os.path.join(exp, "log.txt")): log = open(os.path.join(exp, "log.txt"), encoding="utf-8", errors="ignore").read()
    scen = len([l for l in log.splitlines() if re.match(r"\s+scenario -?\d+ '", l)])
    ready = bool(exp) and os.path.exists(os.path.join(exp, "scenarios.csv"))
    failed = "FAILED" in log or state == "failed" or (state == "done" and not ready)
    started = os.path.getmtime(of) if os.path.exists(of) else (os.path.getmtime(jf) if os.path.exists(jf) else None)
    return dict(job=name, tag=tag, state="failed" if failed else ("ready" if ready and state == "done" else state), exit=code,
                scenarios_done=scen, ready=ready, error=(next((l for l in log.splitlines() if "FAILED" in l), None) or (txt.strip()[-400:] if failed else None)),
                seconds=round(time.time() - started) if started else None)


def jobs():
    names = set()
    for sub in ("jobs", "done"):
        d = os.path.join(BRIDGE, sub)
        if os.path.isdir(d): names |= {f[:-4] for f in os.listdir(d) if f.startswith("w19x_") and f.endswith(".ps1")}
    return sorted((job(n) for n in names), key=lambda j: j["job"], reverse=True)[:20]
