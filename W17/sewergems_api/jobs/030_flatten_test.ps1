. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
$work = 'C:\IbriWork\scratch_flat'
New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw', 'C:\IbriWork\W17\IBRI_W17_R0.stsw.sqlite' $work -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R0.stsw")
  $before = [Flatten]::Snapshot($m, 279727, $log)
  [Flatten]::MergeChain($m, 279727, $log)
  $after = [Flatten]::Snapshot($m, 6, $log)
  [void][Flatten]::Compare($before, $after, $log)
  $am = $m.DomainDataSet.AlternativeManager($m.DomainDataSet.DomainDataSetType().AlternativeType('Physical').Id)
  $log.WriteLine('  physical alternatives left: ' + (($am.Elements() | % { "$($_.Id):$($_.Label)" }) -join ', '))
  foreach ($s in $m.DomainDataSet.ScenarioManager.Elements()) { $log.WriteLine("  scenario $($s.Label) physical=" + $s.AlternativeID('Physical')) }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
