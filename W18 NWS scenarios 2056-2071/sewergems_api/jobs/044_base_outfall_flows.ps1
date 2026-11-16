. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Outfall peak flows with no transfers, every year, on a scratch copy of R4 (flows do not depend on pipe sizes in a steady run).
$out = '\\VBOXSVR\VBOX\bridge\out\f0'; New-Item -ItemType Directory -Force $out | Out-Null
$work = 'C:\IbriWork\scratch_f0'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R4.stsw', 'C:\IbriWork\W17\IBRI_W17_R4.stsw.sqlite' $work -Force
$log = New-Object IO.StringWriter
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R4.stsw")
  $m.DomainDataSet.ScenarioManager.Element(279744).CalculationOptionsID('DelawareProductEngine', 279786)   # 2070 as analysis, scratch only
  foreach ($p in @(@(279763,'2030'), @(279764,'2040'), @(279765,'2050'), @(279766,'2055'), @(279767,'2060'), @(279744,'2070'))) {
    $s = $m.Scenarios.Element($p[0]); $m.SetActiveScenario($s); $t0 = Get-Date
    try { $s.Run() } catch { }
    $d = [Transfer]::OutfallFlows($m)
    ($d.GetEnumerator() | % { "{0},{1}" -f $_.Key, $_.Value }) -join "`n" | Set-Content "$out\f0_$($p[1]).csv"
    $log.WriteLine(("  {0}: {1:n0} s, {2} outfalls" -f $p[1], ((Get-Date) - $t0).TotalSeconds, $d.Count))
  }
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
