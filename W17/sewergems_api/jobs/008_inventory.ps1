. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\inv'
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
    $sw = New-Object IO.StringWriter
    [Inventory]::Run($m, $out, $sw)
    [IO.File]::WriteAllText("$out\inventory.txt", $sw.ToString(), (New-Object Text.UTF8Encoding($false)))
    "done"
    $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
