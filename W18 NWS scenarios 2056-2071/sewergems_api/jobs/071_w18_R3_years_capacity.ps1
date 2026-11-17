# W18 R3: the six year alternatives reloaded with the loads of 2026-11-17 (growth plots 200-3,000 m2, any zoning but
# agricultural / heritage / industrial, not odd-shaped; capacity = 2026 population + growth plots x the team's
# properties per plot x 4.8). Same route as 069, which proved it: W17 R8 -> six LoadBuilder year alternatives renamed
# W18-2031 ... W18-2071 and set from the file (SetYear throws if a stored total differs from the file), then a child
# scenario per year and the outfall flows. A NEW revision: R0 (job 069) and R2 (job 070, SC1 on R0) stay as the record.
# Outfall flows go to out\w18\f0, which py/routing.py reads; 069's were archived to out\w18\f0_R0 on the host first.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads_cap.csv'
$src = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R3.stsw'
New-Item -ItemType Directory -Force 'C:\IbriWork\W18' | Out-Null
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R3*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $BASE2070 = 279744; $UNIT = 279741
$map = [ordered]@{ '2031' = 279769; '2051' = 279770; '2056' = 279771; '2061' = 279772; '2066' = 279773; '2071' = 14 }
function Flush { [IO.File]::WriteAllText("$out\log_071.txt", $log.ToString()) }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet
  $am = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType('SanitaryLoading').Id)
  $log.WriteLine('== the six year alternatives take the W18 years (loads of 2026-11-17)')
  foreach ($y in $map.Keys) {
    $el = $am.Element($map[$y])
    $log.WriteLine(("  alternative {0} '{1}' (parent {2}) -> W18-{3}" -f $map[$y], $el.Label, $el.ParentID, $y))
    [YearLoads]::SetYear($m, $map[$y], $UNIT, $csv, "Q_$y", $log)
    $el.Label = "W18-$y"
    $m.Save(); Flush
  }
  $log.WriteLine('== outfall flows per year, no transfers, base physical, analysis')
  foreach ($y in $map.Keys) {
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['SanitaryLoading'] = $map[$y]
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
