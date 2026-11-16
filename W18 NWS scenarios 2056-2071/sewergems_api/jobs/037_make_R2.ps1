. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R2: plot loads as peaked unit loads (discharge-based, 1 m3/d per unit) in all six sanitary alternatives.
$log = New-Object IO.StringWriter
$src = 'C:\IbriWork\W17\IBRI_W17_R1.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R2.stsw'
$out = '\\VBOXSVR\VBOX\bridge\out\r2'; New-Item -ItemType Directory -Force $out | Out-Null
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  [Convert2]::SetUnitLoad($m, 279741, 'Plot average flow (1 m3/d per unit)', $log)
  foreach ($a in 14, 279769, 279770, 279771, 279772, 279773) { [Convert2]::ConvertAlternative($m, $a, 279741, $log) }
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }

# verification on a scratch copy: 2030 and 2070 run as ANALYSIS, then a 100 L/s pattern-load transfer
$ok = $log.ToString() -notmatch 'FAILED'
if ($ok) {
  $work = 'C:\IbriWork\scratch_r2'; New-Item -ItemType Directory -Force $work | Out-Null
  Copy-Item $dst, "$dst.sqlite" $work -Force
  [void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
  try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R2.stsw")
    function RunExport($sid, $file) { $s = $m.Scenarios.Element($sid); $m.SetActiveScenario($s); try { $s.Run() } catch { }
      $d = [Transfer]::OutfallFlows($m); ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\$file" }
    RunExport 279763 'outfalls_2030.csv'
    $s70 = $m.DomainDataSet.ScenarioManager.Element(279744); $s70.CalculationOptionsID('DelawareProductEngine', 279786)
    RunExport 279744 'outfalls_2070_analysis.csv'
    $o13 = ($m.Network.Manholes.Elements() | ? { $_.Label -eq 'O13-M1' }).Id
    [Transfer]::AddPatternLoad($m, 279769, $o13, 100 * [Transfer]::CFS_PER_LPS, $log)
    RunExport 279763 'outfalls_2030_plus100_O13.csv'
    $m.Close()
  } catch { $log.WriteLine('VERIFY FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R1.stsw.dwh" "$share\IBRI_W17_R2.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R1.stsw.profiles.dwh" "$share\IBRI_W17_R2.stsw.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
