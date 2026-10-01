. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R1: the 2070 physical alternative folded into Base Physical (named 2070), with empty children S1-2070 ... S7-2070.
$log = New-Object IO.StringWriter
$src = 'C:\IbriWork\W17\IBRI_W17_R0.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R1.stsw'
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $before = [Flatten]::Snapshot($m, 279727, $log)
  [Flatten]::MergeChain($m, 279727, $log)
  $after = [Flatten]::Snapshot($m, 6, $log)
  [void][Flatten]::Compare($before, $after, $log)
  [Housekeeping]::RenameAlternative($m, 'Physical', 6, '2070', $log)
  [Flatten]::AddChildren($m, 6, [string[]]@('S1-2070','S2-2070','S3-2070','S4-2070','S5-2070','S6-2070','S7-2070'), $log)
  $m.Save()
  $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText('\\VBOXSVR\VBOX\bridge\out\inv\r1_log.txt', $log.ToString())
if ($log.ToString() -notmatch 'FAILED') {
  $share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
  Copy-Item $dst, "$dst.sqlite" $share -Force
  Copy-Item "$share\IBRI_W17_R0.stsw.dwh" "$share\IBRI_W17_R1.stsw.dwh" -Force
  Copy-Item "$share\IBRI_W17_R0.stsw.profiles.dwh" "$share\IBRI_W17_R1.stsw.profiles.dwh" -Force
}
$log.ToString() -split "`n" | ? { $_ -notmatch '^\s+merged' }
