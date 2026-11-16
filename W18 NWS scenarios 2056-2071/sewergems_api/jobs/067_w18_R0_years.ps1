# W18 R0, seventh attempt: as 066, on loads where every plot sits on a manhole that has a load row (066 failed
# because 6,499 plots had no manhole, HMINNODE = 0, and inserting a row on an unloaded manhole throws).
# Sixth attempt's notes: 060, 062, 063 and 065 all loaded the first NEW year alternative and then failed reading the
# second (GetParentID, "Value does not fall within the expected range"), even after reopening the model: once one new
# child of the 2070 loads holds local records, a sibling without records cannot be read. W17 never created year
# alternatives; it edited the six that LoadBuilder made, which hold a local record on every loaded manhole. So W18
# reuses those six for the six years the design-year search needs, renamed:
#   2030 -> W18-2031 (the self-cleansing check), 2040 -> W18-2051, 2050 -> W18-2056, 2055 -> W18-2061,
#   2060 -> W18-2066, 2070 -> W18-2071 (edited last). SetYear throws if any stored total differs from the file.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads.csv'
$src = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R0.stsw'
New-Item -ItemType Directory -Force 'C:\IbriWork\W18' | Out-Null
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R0*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $BASE2070 = 279744; $UNIT = 279741
$map = [ordered]@{ '2031' = 279769; '2051' = 279770; '2056' = 279771; '2061' = 279772; '2066' = 279773; '2071' = 14 }
function Flush { [IO.File]::WriteAllText("$out\log_067.txt", $log.ToString()) }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet
  $am = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType('SanitaryLoading').Id)
  $log.WriteLine('== the six year alternatives take the W18 years')
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
