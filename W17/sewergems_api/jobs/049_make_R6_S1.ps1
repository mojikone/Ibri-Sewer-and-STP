. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R6: S1 designed until no pipe size changes, then the analysis years; exports read the real catalogue sizes.
$name = 'S1'
$src = 'C:\IbriWork\W17\IBRI_W17_R5.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R6.stsw'
$out = "\\VBOXSVR\VBOX\bridge\out\scen\$name"
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W17' -Filter 'IBRI_W17_R6.stsw*' | Remove-Item -Force
$sc = @{ '2070' = 279800; '2030' = 279801; '2040' = 279802; '2050' = 279803; '2055' = 279804; '2060' = 279805 }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $m.SetActiveScenario($m.Scenarios.Element(279744)); [Scen]::Export($m, $out, 'base2070_inputs', $log)
  $log.WriteLine('== design S1-2070 until stable')
  [Scen]::DesignUntilStable($m, $sc['2070'], 6, $log)
  [Scen]::Export($m, $out, "$name-2070", $log)
  $m.Save()
  $log.WriteLine('== analysis years')
  foreach ($y in '2030','2040','2050','2055','2060') { [Scen]::Run($m, $sc[$y], $log); [Scen]::Export($m, $out, "$name-$y", $log) }
  $m.SetActiveScenario($m.Scenarios.Element($sc['2070']))
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R5.stsw.dwh" "$share\IBRI_W17_R6.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R5.stsw.profiles.dwh" "$share\IBRI_W17_R6.stsw.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log_R6.txt", $log.ToString())
$log.ToString()
