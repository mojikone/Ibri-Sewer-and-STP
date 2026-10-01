. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch_r4\IBRI_W17_R4.stsw')
  [DesignProbe]::Run($m, $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
New-Item -ItemType Directory -Force '\\VBOXSVR\VBOX\bridge\out\design' | Out-Null
[IO.File]::WriteAllText('\\VBOXSVR\VBOX\bridge\out\design\design_probe.txt', $log.ToString())
'done'
