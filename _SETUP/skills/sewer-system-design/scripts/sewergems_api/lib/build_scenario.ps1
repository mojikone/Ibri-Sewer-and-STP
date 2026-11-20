# W18: build one STP scenario for one design year in a model revision: a physical child for the design, sanitary
# children with the transfers for the design year and the check years, the design scenario (flow check first as an
# analysis, then DESIGN until no size changes), an analysis of the design year and of every check year on the designed
# pipes, exports, and a guard that the analyses never change a pipe size. Calculation options and alternatives local.
# Called by a job after setting: $name (SC1..SC4), $dy (design year, '2056'), $checks (e.g. @('2031')), $src, $dst
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$tag = "$name-$dy"
$out = "\\VBOXSVR\VBOX\bridge\out\w18\scen\$tag"; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$DESIGN = 31; $ANALYSIS = 279786; $LOADS2070 = 14; $BASE2070 = 279744; $S1PHYS = 279787
New-Item -ItemType Directory -Force (Split-Path $dst) | Out-Null
Get-ChildItem (Split-Path $dst) -Filter ((Split-Path $dst -Leaf) + '*') | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $dds = $m.DomainDataSet
  $pam = $dds.AlternativeManager($dds.DomainDataSetType().AlternativeType('Physical').Id)
  $basePhys = $pam.Element($S1PHYS).ParentID
  $phys = [Scen]::ChildAlternative($m, 'Physical', $basePhys, $tag, $log)
  $log.WriteLine('== sanitary children with the transfers')
  $san = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  # the six LoadBuilder year alternatives carry the W18 years since job 066 (new year alternatives cannot be read
  # once a sibling holds records, a SewerGEMS fault met by jobs 060-065)
  $W18ALT = @{ '2031' = 279769; '2051' = 279770; '2056' = 279771; '2061' = 279772; '2066' = 279773; '2071' = 14 }
  foreach ($y in @($dy) + $checks) {
    if (-not $W18ALT.ContainsKey($y)) { throw "no W18 year alternative for $y" }
    $san[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $W18ALT[$y], "$name-$y", $log)
  }
  [Scen]::AddTransfers($m, $san, "$out\transfers_$tag.csv", $log)
  $log.WriteLine('== scenarios')
  $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['Physical'] = $phys; $a['SanitaryLoading'] = $san[$dy]
  $sd = [Scen]::ChildScenario($m, $BASE2070, $tag, $a, $ANALYSIS, $log)
  $log.WriteLine('== flow check (design year as analysis on the modeller''s pipes)')
  [Scen]::Run($m, $sd, $log); [Scen]::Export($m, $out, "check$dy", $log)
  [void][Scen]::ChildScenario($m, $BASE2070, $tag, $a, $DESIGN, $log)
  $none = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  $sda = [Scen]::ChildScenario($m, $sd, "$tag" + 'A', $none, $ANALYSIS, $log)
  $kids = [ordered]@{}
  foreach ($y in $checks) { $b = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $b['SanitaryLoading'] = $san[$y]; $kids[$y] = [Scen]::ChildScenario($m, $sd, "$tag-at-$y", $b, $ANALYSIS, $log) }
  $log.WriteLine("== design $dy until no size changes")
  [Scen]::DesignUntilStable($m, $sd, 8, $log)
  [Scen]::Export($m, $out, $tag, $log)
  $m.Save()
  $sizes = [Scen]::Sizes($m)
  $log.WriteLine('== analysis of the design year and the check years on the designed pipes')
  [Scen]::Run($m, $sda, $log); [Scen]::Export($m, $out, "$tag" + 'a', $log)
  foreach ($y in $kids.Keys) { [Scen]::Run($m, $kids[$y], $log); [Scen]::Export($m, $out, "$tag-at-$y", $log) }
  $after = [Scen]::Sizes($m); $moved = 0; foreach ($k in $sizes.Keys) { if ($sizes[$k] -ne $after[$k]) { $moved++ } }
  if ($moved -gt 0) { $log.WriteLine("FAILED: the analysis runs changed $moved pipe sizes") } else { $log.WriteLine('  pipe sizes unchanged by the analysis runs') }
  $m.SetActiveScenario($m.Scenarios.Element($sd))
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log_$tag.txt", $log.ToString())
$log.ToString()
