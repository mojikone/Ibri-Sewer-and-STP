# W18 R0, fifth attempt (064 never ran: the shell that wrote it turned \\VBOXSVR into \VBOXSVR).
# 060, 062 and 063 all loaded the first year and then failed reading the SECOND year's loads (GetParentID, "Value does
# not fall within the expected range"), even with every alternative created and saved first. So the model is closed
# and reopened between years: one year's loads per open model.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads.csv'
$src = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'
New-Item -ItemType Directory -Force 'C:\IbriWork\W18' | Out-Null
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R0*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $LOADS2070 = 14; $BASE2070 = 279744; $UNIT = 279741
$years = 2026, 2031, 2036, 2041, 2046, 2051, 2056, 2061, 2066, 2071
function Flush { [IO.File]::WriteAllText("$out\log_065.txt", $log.ToString()) }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $alt = @{}
  foreach ($y in $years) { $alt[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $LOADS2070, "W18-$y", $log) }
  $m.Save(); $m.Close(); Flush
  $log.WriteLine('== year loads, the model reopened for each year')
  foreach ($y in $years) {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
    [YearLoads]::SetYear($m, $alt[$y], $UNIT, $csv, "Q_$y", $log)
    $m.Save(); $m.Close(); Flush
  }
  $log.WriteLine('== outfall flows per year, no transfers, base physical, analysis')
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($dst)
  foreach ($y in $years) {
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['SanitaryLoading'] = $alt[$y]
    $s = [Scen]::ChildScenario($m, $BASE2070, "W18-$y", $a, $ANALYSIS, $log)
    $t0 = Get-Date
    [Scen]::Run($m, $s, $log)
    $d = [Transfer]::OutfallFlows($m)
    ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\f0_$y.csv"
    $log.WriteLine(("  {0}: run {1:n0} s, {2} outfalls" -f $y, ((Get-Date) - $t0).TotalSeconds, $d.Count)); Flush
  }
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
Flush
$log.ToString()
