. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
function Ids($f) { $l = New-Object 'System.Collections.Generic.List[int]'; Get-Content $f | % { $l.Add([int]$_) }; ,$l }
function Flows($m, $tag) { $d = [Transfer]::OutfallFlows($m); foreach ($k in 'O9','O12') { $log.WriteLine(('  {0} {1}: {2:n2} L/s' -f $tag, $k, ($d[$k] / 86.4))) } }
function RunS($m) { $s = $m.Scenarios.Element(279763); $m.SetActiveScenario($s); try { $s.Run() } catch { $log.WriteLine('  run warnings') } }
$work = 'C:\IbriWork\scratch_unit'
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw', 'C:\IbriWork\W17\IBRI_W17_R0.stsw.sqlite' $work -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R0.stsw")
  RunS $m; Flows $m 'pattern loads'
  [void][Transfer]::ConvertToUnitLoad($m, 279769, (Ids '\\VBOXSVR\VBOX\bridge\out\peak\o9_ids.txt'), 279741, 0, 1.0, $log)
  [void][Transfer]::ConvertToUnitLoad($m, 279769, (Ids '\\VBOXSVR\VBOX\bridge\out\peak\o12_ids.txt'), 279741, 1, 1.0, $log)
  RunS $m; Flows $m 'unit loads (O9 def 0, O12 def 1)'
  foreach ($id in (Get-Content '\\VBOXSVR\VBOX\bridge\out\peak\o9_ids.txt' | Select-Object -First 40)) {
    $sw2 = New-Object IO.StringWriter; [Transfer]::DumpRows($m, 'SanitaryLoading', 'SanitaryLoads', 279769, [int]$id, $sw2)
    if ($sw2.ToString() -match 'row:') { $log.WriteLine($sw2.ToString()); break } }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
