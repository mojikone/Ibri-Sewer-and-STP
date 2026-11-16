. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
function Flows($m, $tag) { $d = [Transfer]::OutfallFlows($m); foreach ($k in 'O10','O13','O1') { $log.WriteLine(('  {0} {1}: {2:n2} L/s' -f $tag, $k, ($d[$k] / 86.4))) } }
function RunS($m) { $s = $m.Scenarios.Element(279763); $m.SetActiveScenario($s); try { $s.Run() } catch { } }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch_run\IBRI_W17_R0.stsw')
  RunS $m; Flows $m 'before'
  [Transfer]::AddFixedInflow($m, 11, 22070, 100 * [Transfer]::CFS_PER_LPS, 0, $log)
  [Transfer]::DumpRows($m, 'InfiltrationAndInflow', 'InflowList', 11, 22070, $log)
  [Transfer]::AddPatternLoad($m, 279769, 278715, 100 * [Transfer]::CFS_PER_LPS, $log)
  [Transfer]::DumpRows($m, 'SanitaryLoading', 'SanitaryLoads', 279769, 278715, $log)
  RunS $m; Flows $m 'after +100 L/s (O13 fixed inflow, O10 pattern load)'
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
