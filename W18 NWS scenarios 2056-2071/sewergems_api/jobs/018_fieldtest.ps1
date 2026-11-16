. \\VBOXSVR\VBOX\bridge\lib\load.ps1
Copy-Item 'C:\IbriWork\M13b\IBRI_3_9_2026_12M.stsw*' 'C:\IbriWork\scratch\' -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force C:\IbriWork\scratch | Out-Null
foreach ($f in 'IBRI_3_9_2026_12M.stsw','IBRI_3_9_2026_12M.stsw.sqlite') { Copy-Item "C:\IbriWork\M13b\$f" C:\IbriWork\scratch -Force }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try { $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\scratch\IBRI_3_9_2026_12M.stsw'); $sw = New-Object IO.StringWriter; [FieldTest]::Try($m, $sw); $sw.ToString(); $m.Close() }
catch { "FAILED: " + $_.Exception.ToString() } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
