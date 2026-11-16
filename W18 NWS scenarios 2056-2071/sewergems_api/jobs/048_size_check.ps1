. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$log = New-Object IO.StringWriter
$work = 'C:\IbriWork\scratch_sizes'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R5.stsw', 'C:\IbriWork\W17\IBRI_W17_R5.stsw.sqlite' $work -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R5.stsw")
  [SizeCheck]::Compare($m, 6, 279787, '\\VBOXSVR\VBOX\bridge\out\scen\S1\sizes_base_vs_S1.csv', $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
