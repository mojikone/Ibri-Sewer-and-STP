. \\VBOXSVR\VBOX\bridge\lib\load.ps1
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try { $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch_run\IBRI_W17_R0.stsw'); $sw = New-Object IO.StringWriter; [CalcOpts]::Dump($m, 'DelawareProductEngine', $sw); [IO.File]::WriteAllText('\\VBOXSVR\VBOX\bridge\out\peak\calcopts.txt', $sw.ToString()); $m.Close() }
catch { 'FAILED: ' + $_.Exception.ToString() } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
