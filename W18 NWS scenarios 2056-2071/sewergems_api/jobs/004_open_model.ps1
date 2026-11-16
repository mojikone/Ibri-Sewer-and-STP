# Open the working copy through the API (read only: nothing is saved) and summarise it.
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.StormSewer.dll'))
$sw = [Diagnostics.Stopwatch]::StartNew()
"== licence: " + [OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
    "== opened in {0:n1} s" -f $sw.Elapsed.TotalSeconds
    "== model members: " + (($m | Get-Member -MemberType Property | Select-Object -ExpandProperty Name) -join ', ')
    "== active scenario: " + $m.ActiveScenario.Label + " (id " + $m.ActiveScenario.Id + ")"
    "== scenarios"
    foreach ($s in $m.Scenarios.Elements()) { "  {0,8}  {1}" -f $s.Id, $s.Label }
    "== network element counts"
    $net = $m.Network
    foreach ($p in ($net | Get-Member -MemberType Property | Select-Object -ExpandProperty Name)) {
        try { $c = $net.$p.Count; "  {0,-28} {1}" -f $p, $c } catch { "  {0,-28} ?" -f $p }
    }
    $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
