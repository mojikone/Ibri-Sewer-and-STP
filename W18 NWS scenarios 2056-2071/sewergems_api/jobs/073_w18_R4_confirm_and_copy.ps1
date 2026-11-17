# W18 R4, read only (engineer, 2026-11-17: "confirm the loads are unit loads at the manholes so the peak applies, and the
# 720 L/km/day infiltration"): lib\Confirm.cs on scenarios W18-2031, W18-2056 and W18-2091, model closed WITHOUT saving;
# then the model files are copied to the bridge for the deliverable zip (out\w18\model_R4\). Nothing in C:\IbriWork changes.
. \\VBOXSVR\VBOX\bridge\lib\load.ps1
$out = '\\VBOXSVR\VBOX\bridge\out\w18\model_R4'; New-Item -ItemType Directory -Force $out | Out-Null
$src = 'C:\IbriWork\W18\IBRI_W18_R4.stsw'
$log = New-Object IO.StringWriter
function Flush { [IO.File]::WriteAllText('\\VBOXSVR\VBOX\bridge\out\w18\confirm_R4.txt', $log.ToString()) }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  [Confirm]::Run($m, [string[]]@('W18-2031', 'W18-2056', 'W18-2091'), $log)
  $m.Close(); Flush
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.WriteLine('== model files copied')
Get-ChildItem 'C:\IbriWork\W18' -Filter 'IBRI_W18_R4*' | ForEach-Object {
  Copy-Item $_.FullName $out -Force
  $log.WriteLine(('  {0}  {1:n1} MB' -f $_.Name, ($_.Length / 1MB)))
}
Flush
$log.ToString()
