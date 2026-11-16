# W18 R0, second attempt (060 failed on the second year: after a run and a save, reading a NEW alternative's loads
# threw "Value does not fall within the expected range" in GetParentID). Here every year alternative is created and
# loaded first, with no run in between (the path that worked for 2026), the model saved, and only then the scenarios
# are created and run, each outfall's own peak flow exported per year.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads.csv'
$src = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'
New-Item -ItemType Directory -Force 'C:\IbriWork\W18' | Out-Null
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R0*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $LOADS2070 = 14; $BASE2070 = 279744; $UNIT = 279741
$years = 2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066, 2071
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $alt = @{}
  $log.WriteLine('== year loads')
  foreach ($y in $years) {
    $alt[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $LOADS2070, "W18-$y", $log)
    [YearLoads]::SetYear($m, $alt[$y], $UNIT, $csv, "Q_$y", $log)
  }
  $m.Save(); $log.WriteLine('  saved after the loads')
  [IO.File]::WriteAllText("$out\log_062.txt", $log.ToString())
  $log.WriteLine('== outfall flows per year, no transfers, base physical, analysis')
  foreach ($y in $years) {
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['SanitaryLoading'] = $alt[$y]
    $s = [Scen]::ChildScenario($m, $BASE2070, "W18-$y", $a, $ANALYSIS, $log)
    $t0 = Get-Date
    [Scen]::Run($m, $s, $log)
    $d = [Transfer]::OutfallFlows($m)
    ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\f0_$y.csv"
    $log.WriteLine(("  {0}: run {1:n0} s, {2} outfalls" -f $y, ((Get-Date) - $t0).TotalSeconds, $d.Count))
    [IO.File]::WriteAllText("$out\log_062.txt", $log.ToString())
  }
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log_062.txt", $log.ToString())
$log.ToString()
