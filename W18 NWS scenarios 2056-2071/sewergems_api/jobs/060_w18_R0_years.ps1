# W18 R0: the NWS year loads (2026-2071, every five years) as sanitary alternatives under the 2070 loads of the
# Colebrook model R8, and each outfall's own peak flow per year with no transfers (base physical, analysis), which the
# transfers of every scenario are built from. Guest copy only; nothing is delivered to the model share.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads.csv'
$src = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'
New-Item -ItemType Directory -Force 'C:\IbriWork\W18' | Out-Null
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R0*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $LOADS2070 = 14; $BASE2070 = 279744; $UNIT = 279741
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  foreach ($y in 2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066, 2071) {
    $alt = [Scen]::ChildAlternative($m, 'SanitaryLoading', $LOADS2070, "W18-$y", $log)
    [YearLoads]::SetYear($m, $alt, $UNIT, $csv, "Q_$y", $log)
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['SanitaryLoading'] = $alt
    $s = [Scen]::ChildScenario($m, $BASE2070, "W18-$y", $a, $ANALYSIS, $log)
    $t0 = Get-Date
    [Scen]::Run($m, $s, $log)
    $d = [Transfer]::OutfallFlows($m)
    ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\f0_$y.csv"
    $log.WriteLine(("  {0}: run {1:n0} s, {2} outfalls" -f $y, ((Get-Date) - $t0).TotalSeconds, $d.Count))
    $m.Save()
  }
  $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log_060.txt", $log.ToString())
$log.ToString()
