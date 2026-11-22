# W19 G7 loads, step 1 (probe): how the loads of a scenario come back through the documented API - every column of
# every sanitary-load row of one scenario, and the support elements that define unit loads, peaking (Extreme Flow
# Setup) and infiltration. Read-only: works on a copy.
$src = 'C:\IbriWork\W18\final\IBRI_SC1-2056_final.stsw'
$tag = 'SC1-2056_final'
$scenarioLabel = 'SC1-2056 design'
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\export\$tag\loads_probe"; New-Item -ItemType Directory -Force $out | Out-Null
$work = "C:\IbriWork\W19\export\$tag-loads.stsw"; New-Item -ItemType Directory -Force (Split-Path $work) | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($work)
  $s = $m.DomainDataSet.ScenarioManager.Elements() | Where-Object { $_.Label -eq $scenarioLabel } | Select-Object -First 1
  $log.WriteLine(('scenario {0} {1}' -f $s.Id, $s.Label))
  [LoadsDump]::SanitaryRows($m, $s.Id, "$out\sanitary_rows.csv", $log)
  [LoadsDump]::SupportLoads($m, "$out\support_loads.csv", $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
