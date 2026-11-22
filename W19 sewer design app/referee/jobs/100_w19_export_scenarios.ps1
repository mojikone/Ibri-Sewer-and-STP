# W19 G7: export EVERY scenario of a SewerGEMS model through the documented OpenFlows API, for the app to load
# (elements, attributes and the results each scenario holds), with no change to the model: it opens a COPY.
# Set $src (the model, inside the guest), $tag (an output folder name) and $run ($false: export the results the model
# already holds; $true: run each scenario's analysis first, saved to the copy only).
$src = 'C:\IbriWork\W18\final\IBRI_SC1-2056_final.stsw'
$tag = 'SC1-2056_final'
$run = $false
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w19\export\$tag"; New-Item -ItemType Directory -Force $out | Out-Null
$work = "C:\IbriWork\W19\export\$tag.stsw"; New-Item -ItemType Directory -Force (Split-Path $work) | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($work)
  $sm = $m.DomainDataSet.ScenarioManager
  $rows = @('id,label,parent,file')
  [Geometry]::Export($m, "$out\geometry.tsv", $log)
  $k = 0
  foreach ($s in $sm.Elements()) {
    $k += 1; $file = 's{0:000}' -f $k
    $rows += ('{0},"{1}",{2},{3}' -f $s.Id, ($s.Label -replace '"', "'"), $s.ParentID, $file)
    $m.SetActiveScenario($m.Scenarios.Element($s.Id))
    if ($run) { [Scen]::Run($m, $s.Id, $log) }
    [Scen]::Export($m, $out, $file, $log)
    $log.WriteLine(("  scenario {0} '{1}' -> {2}" -f $s.Id, $s.Label, $file))   # parentheses: -f inside a call's arguments
  }
  [IO.File]::WriteAllLines("$out\scenarios.csv", $rows)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
