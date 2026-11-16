. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\inv_w17'
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\W17\IBRI_W17_R0.stsw')
    $sw = New-Object IO.StringWriter
    [Inventory]::Run($m, $out, $sw)
    [IO.File]::WriteAllText("$out\inventory.txt", $sw.ToString(), (New-Object Text.UTF8Encoding($false)))
    "done"
    $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }

