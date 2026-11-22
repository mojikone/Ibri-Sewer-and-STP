# W19 G7 loads, step 2: the loads of EVERY scenario of a model already exported by job 100/101 (same $tag, same
# scenario order), per element in m3/d (unit loads and pattern loads), and the load and peaking support elements once,
# so the app can re-solve the model with its own engine. Read-only: works on a copy.
$src = 'C:\IbriWork\W18\final\IBRI_SC1-2056_final.stsw'
$tag = 'SC1-2056_final'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\export\$tag"; New-Item -ItemType Directory -Force $out | Out-Null
$work = "C:\IbriWork\W19\export\$tag-loads2.stsw"; New-Item -ItemType Directory -Force (Split-Path $work) | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($work)
  [LoadsDump]::SupportLoads($m, "$out\support_loads.csv", $log)
  $k = 0
  foreach ($s in $m.DomainDataSet.ScenarioManager.Elements()) {
    $k += 1; $file = 's{0:000}' -f $k
    [LoadsDump]::ScenarioLoads($m, $s.Id, "$out\loads_$file.csv", $log)
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log_loads.txt", $log.ToString())
