# W19 (2026-11-23): what the engineer's pond model holds - every element type, field, geometry, the calculation options
# and the results of a run - read through the API from a copy (the model in the bridge share is not touched).
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$src = '\\VBOXSVR\VBOX\bridge\models\Pond_Mouj\Pond_Mouj.stsw'
$dir = 'C:\IbriWork\W19\src\Pond_Mouj_dump'; New-Item -ItemType Directory -Force $dir | Out-Null
$out = '\\VBOXSVR\VBOX\bridge\out\w19\pond_dump'; New-Item -ItemType Directory -Force $out | Out-Null
Copy-Item -LiteralPath $src -Destination "$dir\model.stsw" -Force
Copy-Item -LiteralPath "$src.sqlite" -Destination "$dir\model.stsw.sqlite" -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$dir\model.stsw")
  $m.SaveAs("$dir\work.stsw")
  foreach ($s in $m.DomainDataSet.ScenarioManager.Elements()) {
    $log.WriteLine(("scenario {0} '{1}'" -f $s.Id, $s.Label))
    $m.SetActiveScenario($m.Scenarios.Element($s.Id))
    try { [Scen]::Run($m, $s.Id, $log) } catch { $log.WriteLine("  run failed: " + $_.Exception.Message) }
    [ElementDump]::Run($m, $s.Id, "$out\s$($s.Id)", $log)
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
