# W18 final design (engineer, 2026-11-18): one case of the own design put into a copy of R4 - sizes and inverts of every
# conduit, the lifts (station manhole -> 1 m stub -> outfall, the lift's pipe switched off, its flow pumped to the next
# manhole as a transfer), the gravity joins (outfall -> manhole, new sewer to the receiver), every element renamed (pumps
# P#, lifts P#L#), the transfers of the pumps and lifts for the design year and the check years; then an analysis (no
# design run: the sizes are the design) of the design year and of each check year, exports, and a read-back.
# Called by a job after setting: $case (SC1-2056), $name (SC1), $dy ('2056'), $checks (@('2031','2036')), $src, $dst, $in
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = "\\VBOXSVR\VBOX\bridge\out\w18\final\$case"; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$ANALYSIS = 279786; $BASE2070 = 279744; $S1PHYS = 279787
$W18ALT = @{ '2031' = 279769; '2036' = 279800; '2051' = 279770; '2056' = 279771; '2061' = 279772 }
New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
Get-ChildItem (Split-Path $dst) -Filter ((Split-Path $dst -Leaf).Replace('.stsw', '') + '*') -ErrorAction SilentlyContinue | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet
  $pam = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType('Physical').Id)
  $phys = [Scen]::ChildAlternative($m, 'Physical', $pam.Element($S1PHYS).ParentID, "$case design", $log)
  $san = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  foreach ($y in @($dy) + $checks) { $san[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $W18ALT[$y], "$name-$y loads and transfers", $log) }
  [Scen]::AddTransfers($m, $san, "$in\transfers.csv", $log)
  $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['Physical'] = $phys; $a['SanitaryLoading'] = $san[$dy]
  $sd = [Scen]::ChildScenario($m, $BASE2070, "$case design", $a, $ANALYSIS, $log)
  $m.SetActiveScenario($m.Scenarios.Element($sd))
  $log.WriteLine('== the design applied')
  [FinalBuild]::Apply($m, $in, $log)
  $m.Save()
  [FinalBuild]::Check($m, "$out\readback_$case.csv", $log)
  $kids = [ordered]@{}
  foreach ($y in $checks) { $b = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $b['SanitaryLoading'] = $san[$y]; $kids[$y] = [Scen]::ChildScenario($m, $sd, "$case design at the $y peak", $b, $ANALYSIS, $log) }
  $log.WriteLine('== analyses')
  [Scen]::Run($m, $sd, $log); [Scen]::Export($m, $out, "$case", $log)
  foreach ($y in $kids.Keys) { [Scen]::Run($m, $kids[$y], $log); [Scen]::Export($m, $out, "$case-at-$y", $log) }
  $m.SetActiveScenario($m.Scenarios.Element($sd))
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log_$case.txt", $log.ToString())
$log.ToString()
