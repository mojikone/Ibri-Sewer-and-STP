. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Does RunDesign (not Run) resize pipes? Scratch copy of R5, scenario S1-2070.
$work = 'C:\IbriWork\scratch_design'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R5.stsw', 'C:\IbriWork\W17\IBRI_W17_R5.stsw.sqlite' $work -Force
$out = '\\VBOXSVR\VBOX\bridge\out\scen\S1test'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R5.stsw")
  $s = $m.Scenarios.Element(279800); $m.SetActiveScenario($s)
  $log.WriteLine('calc options of S1-2070: ' + $m.DomainDataSet.ScenarioManager.Element(279800).CalculationOptionsID('DelawareProductEngine'))
  $before = @{}; foreach ($c in $m.Network.Conduits.Elements()) { $before[$c.Id] = $c.Input.ConduitDiameter }
  $t0 = Get-Date
  try { $res = $s.RunDesign($null, $null, $false); $log.WriteLine('RunDesign returned ' + $(if ($res) { $res.Length } else { 'null' }) + ' elements') }
  catch { $log.WriteLine('RunDesign raised: ' + $_.Exception.InnerException.GetType().Name + ' ' + $_.Exception.InnerException.Message) }
  $log.WriteLine(('RunDesign took {0:n0} s' -f ((Get-Date) - $t0).TotalSeconds))
  $n = 0; foreach ($c in $m.Network.Conduits.Elements()) { if ([math]::Abs($c.Input.ConduitDiameter - $before[$c.Id]) -gt 1e-6) { $n++ } }
  $log.WriteLine("diameters changed after RunDesign: $n")
  $c2 = $m.Network.Conduits.Elements() | ? { $_.Label -eq 'O1-P2429' }
  $log.WriteLine('O1-P2429 now: ' + $c2.Input.ConduitDiameter + ' mm, ' + $c2.Input.ConduitShapeLabel)
  [Scen]::Export($m, $out, 'after_rundesign', $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
