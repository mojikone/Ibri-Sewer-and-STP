# Read-only: reflect the API surface needed for the housekeeping (alternatives, scenarios, calc options, elements).
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
[void][Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.dll'))
$a = [Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.StormSewer.dll'))
function Show($typeName) {
    $t = $a.GetType($typeName); if (-not $t) { "!! $typeName not found"; return }
    "== $typeName"
    $all = @($t) + $t.GetInterfaces()
    foreach ($it in $all) {
        foreach ($p in $it.GetProperties()) { "  P {0}.{1} : {2}" -f $it.Name, $p.Name, $p.PropertyType.Name }
        foreach ($m in $it.GetMethods() | Where-Object { -not $_.IsSpecialName }) {
            "  M {0}.{1}({2}) : {3}" -f $it.Name, $m.Name, (($m.GetParameters() | ForEach-Object { $_.ParameterType.Name + ' ' + $_.Name }) -join ', '), $m.ReturnType.Name }
    }
}
Show 'OpenFlows.StormSewer.Domain.IStormSewerModel'
$a.GetExportedTypes() | Where-Object { $_.IsInterface -and $_.Name -match 'Alternatives?$|Scenario|CalculationOptions|^IStormSewerAlternatives|ExtremeFlow|PatternLoad|SanitaryLoad|SystemFlow|IOutfall$|IManhole$|IConduit$|IManholeInput$|IOutfallInput$|IConduitInput$|IManholes$|IOutfalls$|IConduits$' } |
    Sort-Object FullName | ForEach-Object { Show $_.FullName }
