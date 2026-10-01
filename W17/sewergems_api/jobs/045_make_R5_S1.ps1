. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R5: option S1 (centralised STP at O-1) built, flow-checked, designed for 2070 and analysed for 2030-2060.
$name = 'S1'
$src = 'C:\IbriWork\W17\IBRI_W17_R4.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R5.stsw'
$out = "\\VBOXSVR\VBOX\bridge\out\scen\$name"; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
$yearAlt = [ordered]@{ '2030' = 279769; '2040' = 279770; '2050' = 279771; '2055' = 279772; '2060' = 279773; '2070' = 14 }
$physS = @{ 'S1' = 279787; 'S2' = 279788; 'S3' = 279789; 'S4' = 279790; 'S5' = 279791; 'S6' = 279792; 'S7' = 279793 }
Get-ChildItem 'C:\IbriWork\W17' -Filter 'IBRI_W17_R5.stsw*' | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $log.WriteLine('== modeller design (base 2070 physical), inputs only')
  $m.SetActiveScenario($m.Scenarios.Element(279744)); [Scen]::Export($m, $out, 'base2070_inputs', $log)
  $log.WriteLine('== catalogue roughness'); [Scen]::SetCatalogueN($m, 0.013, $log)
  $log.WriteLine('== sanitary children with the transfers')
  $san = New-Object 'System.Collections.Generic.Dictionary[string,int]'
  foreach ($y in $yearAlt.Keys) { $san[$y] = [Scen]::ChildAlternative($m, 'SanitaryLoading', $yearAlt[$y], "$name-$y", $log) }
  [Scen]::AddTransfers($m, $san, "$out\transfers_$name.csv", $log)
  $log.WriteLine('== scenarios')
  $a = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $a['Physical'] = $physS[$name]; $a['SanitaryLoading'] = $san['2070']
  $s70 = [Scen]::ChildScenario($m, 279744, "$name-2070", $a, 279786, $log)          # analysis first, for the flow check
  $kids = [ordered]@{}
  foreach ($y in '2030','2040','2050','2055','2060') { $b = New-Object 'System.Collections.Generic.Dictionary[string,int]'; $b['SanitaryLoading'] = $san[$y]; $kids[$y] = [Scen]::ChildScenario($m, $s70, "$name-$y", $b, 279786, $log) }
  $log.WriteLine('== flow check before design (2070 as analysis)')
  [Scen]::Run($m, $s70, $log); [Scen]::Export($m, $out, 'check2070', $log)
  $m.DomainDataSet.ScenarioManager.Element($s70).CalculationOptionsID('DelawareProductEngine', 31)
  $log.WriteLine('== design 2070')
  [Scen]::Run($m, $s70, $log); [Scen]::Export($m, $out, "$name-2070", $log)
  $m.Save(); $log.WriteLine('  saved after design')
  $log.WriteLine('== analysis years')
  foreach ($y in $kids.Keys) { [Scen]::Run($m, $kids[$y], $log); [Scen]::Export($m, $out, "$name-$y", $log) }
  $m.SetActiveScenario($m.Scenarios.Element($s70))
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
if ($log.ToString() -notmatch 'FAILED') {
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R4.stsw.dwh" "$share\IBRI_W17_R5.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R4.stsw.profiles.dwh" "$share\IBRI_W17_R5.stsw.profiles.dwh" -Force
  $log.WriteLine('  delivered to ' + $share)
}
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
