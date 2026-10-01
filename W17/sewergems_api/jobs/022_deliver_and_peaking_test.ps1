. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# 1) deliver the housekeeping model to the shared folder (drawing file and contours carried over from the source copy)
$share = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\14 IBRI_W17'
New-Item -ItemType Directory -Force $share | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw' $share -Force
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw.sqlite' $share -Force
Copy-Item 'C:\IbriWork\M13b\IBRI_3_9_2026_12M.stsw.dwh' "$share\IBRI_W17_R0.stsw.dwh" -Force
Copy-Item 'C:\IbriWork\M13b\IBRI_3_9_2026_12M.stsw.profiles.dwh' "$share\IBRI_W17_R0.stsw.profiles.dwh" -Force
Copy-Item 'C:\IbriWork\M13b\SHP' $share -Recurse -Force
Get-ChildItem $share | % { "{0,12}  {1}" -f $_.Length, $_.Name }

# 2) peaking test on a scratch copy: run 2030 (analysis) and export pipe flows and base loads
$run = 'C:\IbriWork\scratch_run'
Remove-Item -Recurse -Force $run -ErrorAction SilentlyContinue; New-Item -ItemType Directory -Force $run | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw' $run; Copy-Item 'C:\IbriWork\W17\IBRI_W17_R0.stsw.sqlite' $run
$out = '\\VBOXSVR\VBOX\bridge\out\peak'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$run\IBRI_W17_R0.stsw")
  [Peaking]::ExportBaseLoads($m, 279769, "$out\base_2030.csv", $log)
  [Peaking]::RunAndExport($m, 279763, "$out\flows_2030.csv", $log)
  $m.Close()
} catch { $log.WriteLine("FAILED: " + $_.Exception.ToString()) }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession(); [IO.File]::WriteAllText("$out\log.txt", $log.ToString()) }
$log.ToString()
