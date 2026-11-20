# W18 R4: year loads every 5 years from 2031 to 2091 (engineer, 2026-11-17), on the loads of the same day.
# R3 (job 071) holds six year alternatives, the six LoadBuilder made (W18-2031, -2051, -2056, -2061, -2066, -2071).
# The seven missing years (2036, 2041, 2046, 2076, 2081, 2086, 2091) are made by COPYING the loaded 2070 alternative
# (id 14, a local record on every loaded manhole) with IModelingElementManager.Copy(id) - not by Add(parent), which
# jobs 060-065 proved unusable (a new child without local records cannot be read once a sibling holds records:
# GetParentID, "Value does not fall within the expected range"). All copies are made and saved first, then all
# thirteen years are set from the file (SetYear throws if a stored total differs from the file), then a child scenario
# and the outfall flows for each new year. A NEW revision: R3 stays as it is.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$csv = '\\VBOXSVR\VBOX\bridge\data\w18\manhole_loads_2091.csv'
$src = 'C:\IbriWork\W18\IBRI_W18_R3.stsw'; $dst = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R4*' | Remove-Item -Force
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $BASE2070 = 279744; $UNIT = 279741; $LOADED = 14
$old = [ordered]@{ '2031' = 279769; '2051' = 279770; '2056' = 279771; '2061' = 279772; '2066' = 279773; '2071' = 14 }
$newYears = '2036', '2041', '2046', '2076', '2081', '2086', '2091'
function Flush { [IO.File]::WriteAllText("$out\log_072.txt", $log.ToString()) }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet
  $am = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType('SanitaryLoading').Id)
  $src14 = $am.Element($LOADED)
  $log.WriteLine(("== copies of alternative {0} '{1}' (parent {2})" -f $LOADED, $src14.Label, $src14.ParentID))
  $alt = [ordered]@{}
  foreach ($y in $newYears) {
    $id = [int]$am.Copy($LOADED)
    $el = $am.Element($id); $el.Label = "W18-$y"; $alt[$y] = $id
    $log.WriteLine(("  W18-{0}: alternative {1} (parent {2})" -f $y, $id, $el.ParentID))
  }
  $m.Save(); Flush
  $log.WriteLine('== thirteen years set from the file')
  $all = [ordered]@{}
  foreach ($y in (2031..2091 | ? { ($_ - 2031) % 5 -eq 0 })) { $k = "$y"; if ($old.Contains($k)) { $all[$k] = $old[$k] } else { $all[$k] = $alt[$k] } }
  if ($all.Count -ne 13) { throw "expected 13 years, got $($all.Count)" }
  foreach ($y in $all.Keys) {
    [YearLoads]::SetYear($m, $all[$y], $UNIT, $csv, "Q_$y", $log)
    $m.Save(); Flush
  }
  $log.WriteLine('== outfall flows for the new years, no transfers, base physical, analysis')
  foreach ($y in $newYears) {
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['SanitaryLoading'] = $alt[$y]
    $s = [Scen]::ChildScenario($m, $BASE2070, "W18-$y", $a, $ANALYSIS, $log)
    $t0 = Get-Date
    [Scen]::Run($m, $s, $log)
    $d = [Transfer]::OutfallFlows($m)
    ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\f0_$y.csv"
    $log.WriteLine(("  {0}: run {1:n0} s, {2} outfalls" -f $y, ((Get-Date) - $t0).TotalSeconds, $d.Count)); Flush
    $m.Save()
  }
  $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
Flush
$log.ToString()
