# Build several STP options in ONE model revision, one after another, saving after each:
# sanitary children with the transfers, scenarios (2070 design, 2070 analysis check, five analysis years, all set local),
# design until stable, analyses, exports, and a guard that analyses never change pipe sizes.
# Called by a job after setting: $names (array), $src, $dst, $prevShare (revision whose drawing files are copied)
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$yearAlt = [ordered]@{ '2030' = 279769; '2040' = 279770; '2050' = 279771; '2055' = 279772; '2060' = 279773; '2070' = 14 }
$physOf = @{ 'S1' = 279787; 'S2' = 279788; 'S3' = 279789; 'S4' = 279790; 'S5' = 279791; 'S6' = 279792; 'S7' = 279793 }
$DESIGN = 31; $ANALYSIS = 279786
$leaf = Split-Path $dst -Leaf
$runlog = "\\VBOXSVR\VBOX\bridge\out\scen\log_$leaf.txt"
Set-Content $runlog ("start " + (Get-Date -Format o))
Get-ChildItem 'C:\IbriWork\W17' -Filter ($leaf + '*') | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  foreach ($name in $names) {
    $log = New-Object IO.StringWriter
    $out = "\\VBOXSVR\VBOX\bridge\out\scen\$name"; New-Item -ItemType Directory -Force $out | Out-Null
    $log.WriteLine("######## $name  " + (Get-Date -Format T))
    $m.SetActiveScenario($m.Scenarios.Element(279744)); [Scen]::Export($m, $out, 'base2070_inputs', $log)
    $san = New-Object 'System.Collections.Generic.Dictionary[string,int]'
    foreach ($y in $yearAlt.Keys) { $san[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $yearAlt[$y], "$name-$y", $log) }
    [Scen]::AddTransfers($m, $san, "$out\transfers_$name.csv", $log)
    $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['Physical'] = $physOf[$name]; $a['SanitaryLoading'] = $san['2070']
    $s70 = [Scen]::ChildScenario($m, 279744, "$name-2070", $a, $ANALYSIS, $log)
    [Scen]::Run($m, $s70, $log); [Scen]::Export($m, $out, 'check2070', $log)
    [void][Scen]::ChildScenario($m, 279744, "$name-2070", $a, $DESIGN, $log)
    $none = New-Object 'System.Collections.Generic.Dictionary[string,int]'
    $s70a = [Scen]::ChildScenario($m, $s70, "$name-2070A", $none, $ANALYSIS, $log)
    $kids = [ordered]@{}
    foreach ($y in '2030','2040','2050','2055','2060') { $b = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $b['SanitaryLoading'] = $san[$y]; $kids[$y] = [Scen]::ChildScenario($m, $s70, "$name-$y", $b, $ANALYSIS, $log) }
    [Scen]::DesignUntilStable($m, $s70, 8, $log)
    [Scen]::Export($m, $out, "$name-2070", $log)
    $sizes = [Scen]::Sizes($m)
    [Scen]::Run($m, $s70a, $log); [Scen]::Export($m, $out, "$name-2070a", $log)
    foreach ($y in $kids.Keys) { [Scen]::Run($m, $kids[$y], $log); [Scen]::Export($m, $out, "$name-$y", $log) }
    $m.SetActiveScenario($m.Scenarios.Element($s70))
    $after = [Scen]::Sizes($m); $moved = 0; foreach ($k in $sizes.Keys) { if ($sizes[$k] -ne $after[$k]) { $moved++ } }
    if ($moved -gt 0) { $log.WriteLine("FAILED: the analysis runs changed $moved pipe sizes") } else { $log.WriteLine('  pipe sizes unchanged by the analysis runs') }
    $m.Save(); $log.WriteLine("  saved after $name " + (Get-Date -Format T))
    [IO.File]::WriteAllText("$out\log_$leaf.txt", $log.ToString())
    Add-Content $runlog ($log.ToString())
    if ($log.ToString() -match 'FAILED') { break }
  }
  $m.Close()
} catch { Add-Content $runlog ('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ((Get-Content $runlog -Raw) -notmatch 'FAILED') {
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\$prevShare.dwh" "$share\$leaf.dwh" -Force
  Copy-Item "$share\$prevShare.profiles.dwh" "$share\$leaf.profiles.dwh" -Force
  Add-Content $runlog ('delivered to ' + $share)
}
Add-Content $runlog ("end " + (Get-Date -Format o))
Get-Content $runlog
