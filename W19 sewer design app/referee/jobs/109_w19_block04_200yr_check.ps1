# W19 sections, step 6 (check): Block 04's 200-year storm, run first on a copy and exported the app's way, to see
# whether SewerGEMS treats its shape-3 channels as open or closed at the rise.
# W19: export a SewerGEMS model for the app (this job was written by the app). Every scenario: the elements, their
# attributes, the results the model holds, the loads and the peaking support. The model is COPIED first and only the
# copy is opened, so nothing is written beside the modeller's file. scenarios.csv is written last. With $run, every
# scenario is computed first on the copy (a model saved without results then has them; a storm model takes minutes each).
# Boxes and open channels also get sections_<file>.csv (Sections.cs: shape, dimensions, n and their results in SI).
$src = '\\VBOXSVR\Win10_shared_folder\SewerGEMS Block 04 11102026\SewerGEMS Block 04.stsw'
$tag = 'Block04_200yr_check'
$run = $true
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
  foreach ($s in @($sm.Elements() | Where-Object { $_.Label -eq '200 yr' })) {
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
