. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\diag'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\W17\IBRI_W17_R1.stsw')
  [LoadsDiag]::Run($m, $out, 'O15-M72', $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\diag.txt", $log.ToString())
$log.ToString()
