. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# S1 2070 run as an ANALYSIS on the designed pipes (scratch copy of R6), for the d/D and velocity checks.
$work = 'C:\IbriWork\scratch_r6'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R6.stsw', 'C:\IbriWork\W17\IBRI_W17_R6.stsw.sqlite' $work -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R6.stsw")
  $m.DomainDataSet.ScenarioManager.Element(279800).CalculationOptionsID('DelawareProductEngine', 279786)
  [Scen]::Run($m, 279800, $log); [Scen]::Export($m, '\\VBOXSVR\VBOX\bridge\out\scen\S1', 'S1-2070a', $log)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
