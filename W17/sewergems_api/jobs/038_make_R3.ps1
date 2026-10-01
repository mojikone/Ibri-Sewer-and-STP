. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R3: one sanitary load per manhole (rows merged) in all six years; Peltier100-Merriamck gets a 1.001 L/s -> 3.56 row.
$log = New-Object IO.StringWriter
$src = 'C:\IbriWork\W17\IBRI_W17_R2.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R3.stsw'
$out = '\\VBOXSVR\VBOX\bridge\out\r3'; New-Item -ItemType Directory -Force $out | Out-Null
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  foreach ($a in 14, 279769, 279770, 279771, 279772, 279773) { [OneRow]::MergeUnitRows($m, $a, 279741, $log) }
  [OneRow]::AddTableRow($m, 'Peltier100-Merriamck', 1.001, 3.56, $log)
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }

if ($log.ToString() -notmatch 'FAILED') {
  # check on a scratch copy: 2030 and 2070 as analysis, outfall flows to compare with R2
  $work = 'C:\IbriWork\scratch_r3'; New-Item -ItemType Directory -Force $work | Out-Null
  Copy-Item $dst, "$dst.sqlite" $work -Force
  [void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
  try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R3.stsw")
    function RunExport($sid, $file) { $s = $m.Scenarios.Element($sid); $m.SetActiveScenario($s); try { $s.Run() } catch { }
      $d = [Transfer]::OutfallFlows($m); ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\$file" }
    RunExport 279763 'outfalls_2030.csv'
    $m.DomainDataSet.ScenarioManager.Element(279744).CalculationOptionsID('DelawareProductEngine', 279786)
    RunExport 279744 'outfalls_2070_analysis.csv'
    $m.Close()
  } catch { $log.WriteLine('CHECK FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R2.stsw.dwh" "$share\IBRI_W17_R3.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R2.stsw.profiles.dwh" "$share\IBRI_W17_R3.stsw.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
