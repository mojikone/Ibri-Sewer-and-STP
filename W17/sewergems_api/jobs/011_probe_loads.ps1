. \\VBOXSVR\VBOX\bridge\lib\load.ps1
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
    $sw = New-Object IO.StringWriter
    try { [Probe]::Run($m, $sw) } catch { $sw.WriteLine("FAILED in probe: " + $_.Exception.ToString()) }
    [IO.File]::WriteAllText('\\VBOXSVR\VBOX\bridge\out\inv\probe_loads.txt', $sw.ToString(), (New-Object Text.UTF8Encoding($false)))
    "done"
    $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
