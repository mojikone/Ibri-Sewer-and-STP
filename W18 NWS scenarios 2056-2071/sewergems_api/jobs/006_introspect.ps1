# Read-only: inspect live objects so the edit scripts use real member and field names.
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.dll'))
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.StormSewer.dll'))
function Members($o, $title) { "== $title  [" + $o.GetType().FullName + "]"; $o | Get-Member | Where-Object MemberType -in 'Property','Method' | ForEach-Object { "  " + $_.MemberType.ToString().Substring(0,1) + " " + $_.Definition } }
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
    $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open('C:\IbriWork\M13\IBRI_3_9_2026_12M.stsw')
    $c = $m.Network.Conduits.Elements()[0]
    Members $c 'conduit'
    Members $c.Input 'conduit.Input'
    $mh = $m.Network.Manholes.Elements()[0]
    Members $mh 'manhole'
    Members $mh.Input 'manhole.Input'
    $o = $m.Network.Outfalls.Elements()[0]
    Members $o.Input 'outfall.Input'
    Members $m.Alternatives 'model.Alternatives'
    Members $m.Scenarios.Elements()[0] 'scenario'
    Members $m.Network.Manholes.InputFields 'manholes.InputFields'
    "== manhole input field names"
    try { $m.Network.Manholes.InputFields.FieldNames() -join ' | ' } catch { "FieldNames failed: $_" }
    "== conduit input field names"
    try { $m.Network.Conduits.InputFields.FieldNames() -join ' | ' } catch { "FieldNames failed: $_" }
    Members $m.DomainDataSet 'DomainDataSet'
    $m.Close()
} catch { "FAILED: " + $_.Exception.ToString() }
finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
