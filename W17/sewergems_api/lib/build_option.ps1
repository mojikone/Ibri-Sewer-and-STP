# Build one STP option in a model revision: sanitary children with the transfers, scenarios (2070 design, 2070 analysis
# check, five analysis years), design until stable, analyses, exports, and a check that analyses never change pipe sizes.
# Called by a job after setting: $name, $src, $dst, $physId, $prevShare (revision whose drawing files are copied)
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\scen\$name"; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$yearAlt = [ordered]@{ '2030' = 279769; '2040' = 279770; '2050' = 279771; '2055' = 279772; '2060' = 279773; '2070' = 14 }
$DESIGN = 31; $ANALYSIS = 279786
Get-ChildItem 'C:\IbriWork\W17' -Filter ((Split-Path $dst -Leaf) + '*') | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $m.SetActiveScenario($m.Scenarios.Element(279744)); [Scen]::Export($m, $out, 'base2070_inputs', $log)
  [Scen]::SetCatalogueN($m, 0.013, $log)
  $log.WriteLine('== sanitary children with the transfers')
  $san = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  foreach ($y in $yearAlt.Keys) { $san[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $yearAlt[$y], "$name-$y", $log) }
  [Scen]::AddTransfers($m, $san, "$out\transfers_$name.csv", $log)
  $log.WriteLine('== scenarios')
  $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['Physical'] = $physId; $a['SanitaryLoading'] = $san['2070']
  $s70 = [Scen]::ChildScenario($m, 279744, "$name-2070", $a, $ANALYSIS, $log)
  $log.WriteLine('== flow check (2070 as analysis on the modeller''s pipes)')
  [Scen]::Run($m, $s70, $log); [Scen]::Export($m, $out, 'check2070', $log)
  $none = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  [void][Scen]::ChildScenario($m, 279744, "$name-2070", $a, $DESIGN, $log)
  $s70a = [Scen]::ChildScenario($m, $s70, "$name-2070A", $none, $ANALYSIS, $log)
  $kids = [ordered]@{}
  foreach ($y in '2030','2040','2050','2055','2060') { $b = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $b['SanitaryLoading'] = $san[$y]; $kids[$y] = [Scen]::ChildScenario($m, $s70, "$name-$y", $b, $ANALYSIS, $log) }
  $log.WriteLine('== design 2070 until no size changes')
  [Scen]::DesignUntilStable($m, $s70, 8, $log)
  [Scen]::Export($m, $out, "$name-2070", $log)
  $m.Save()
  $sizes = [Scen]::Sizes($m)
  $log.WriteLine('== 2070 analysis check and the analysis years')
  [Scen]::Run($m, $s70a, $log); [Scen]::Export($m, $out, "$name-2070a", $log)
  foreach ($y in $kids.Keys) { [Scen]::Run($m, $kids[$y], $log); [Scen]::Export($m, $out, "$name-$y", $log) }
  $after = [Scen]::Sizes($m); $moved = 0; foreach ($k in $sizes.Keys) { if ($sizes[$k] -ne $after[$k]) { $moved++ } }
  if ($moved -gt 0) { $log.WriteLine("FAILED: the analysis runs changed $moved pipe sizes") } else { $log.WriteLine('  pipe sizes unchanged by the analysis runs') }
  $m.SetActiveScenario($m.Scenarios.Element($s70))
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  $leaf = Split-Path $dst -Leaf
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\$prevShare.dwh" "$share\$leaf.dwh" -Force
  Copy-Item "$share\$prevShare.profiles.dwh" "$share\$leaf.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log_$((Split-Path $dst -Leaf)).txt", $log.ToString())
$log.ToString()
