. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R4: the engineer's LoadBuilder reload (R4_loads) -> diagnosis, then peaked unit loads, one row per manhole.
$share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
$in = 'C:\IbriWork\W17\R4_loads'; New-Item -ItemType Directory -Force $in | Out-Null
foreach ($f in 'IBRI_W17_R4_loads.stsw', 'IBRI_W17_R4_loads.stsw.sqlite') { Copy-Item (Join-Path $share $f) $in -Force }
$out = '\\VBOXSVR\VBOX\bridge\out\r4'; New-Item -ItemType Directory -Force "$out\diag" | Out-Null
$dst = 'C:\IbriWork\W17\IBRI_W17_R4.stsw'
Get-ChildItem 'C:\IbriWork\W17' -Filter 'IBRI_W17_R4.stsw*' | Remove-Item -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$in\IBRI_W17_R4_loads.stsw")
  $m.SaveAs($dst)
  $log.WriteLine('== leftover unit rows (not written by the reload) removed first')
  Set-Content "$out\leftover_rows.csv" 'alt,manhole,rows_removed,m3d,rows_kept'
  foreach ($a in 14, 279769, 279770, 279771, 279772, 279773) { [OneRow]::DeleteRowsOfDefinition($m, $a, 1, "$out\leftover_rows.csv", $log) }
  $log.WriteLine('== conversion')
  foreach ($a in 14, 279769, 279770, 279771, 279772, 279773) { [Convert2]::ConvertAlternative($m, $a, 279741, $log) }
  foreach ($a in 14, 279769, 279770, 279771, 279772, 279773) { [OneRow]::MergeUnitRows($m, $a, 279741, $log) }
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }

if ($log.ToString() -notmatch 'FAILED') {
  $work = 'C:\IbriWork\scratch_r4'; New-Item -ItemType Directory -Force $work | Out-Null
  Copy-Item $dst, "$dst.sqlite" $work -Force
  [void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
  try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R4.stsw")
    function RunExport($sid, $file) { $s = $m.Scenarios.Element($sid); $m.SetActiveScenario($s); try { $s.Run() } catch { }
      $d = [Transfer]::OutfallFlows($m); ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\$file" }
    RunExport 279763 'outfalls_2030.csv'
    $m.DomainDataSet.ScenarioManager.Element(279744).CalculationOptionsID('DelawareProductEngine', 279786)
    RunExport 279744 'outfalls_2070_analysis.csv'
    $m.Close()
  } catch { $log.WriteLine('CHECK FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R4_loads.stsw.dwh" "$share\IBRI_W17_R4.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R4_loads.stsw.profiles.dwh" "$share\IBRI_W17_R4.stsw.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()


