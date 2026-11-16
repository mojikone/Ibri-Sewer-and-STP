$OutputEncoding = [Text.Encoding]::UTF8
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
$d = [Reflection.Assembly]::LoadFrom((Join-Path $bin 'Haestad.Domain.dll'))
$s = [Reflection.Assembly]::LoadFrom((Join-Path $bin 'Haestad.Support.dll'))
function Sig($t) {
    $all = @($t) + $t.GetInterfaces()
    $seen = @{}
    foreach ($it in $all) {
        foreach ($p in $it.GetProperties()) { $k = "P " + $p.Name + " : " + $p.PropertyType.Name; if (-not $seen[$k]) { $seen[$k]=1; "  " + $k } }
        foreach ($m in $it.GetMethods() | Where-Object { -not $_.IsSpecialName }) {
            $k = "M " + $m.Name + "(" + (($m.GetParameters() | % { $_.ParameterType.Name + " " + $_.Name }) -join ", ") + ") : " + $m.ReturnType.Name
            if (-not $seen[$k]) { $seen[$k]=1; "  " + $k } }
    }
}
foreach ($n in 'Haestad.Domain.IDomainDataSetType','Haestad.Domain.IAlternativeType','Haestad.Domain.IAlternativeManager','Haestad.Domain.IAlternative',
               'Haestad.Domain.IScenarioManager','Haestad.Domain.IScenario','Haestad.Domain.IDomainElementManager','Haestad.Domain.IFieldManager',
               'Haestad.Domain.IDomainElementType','Haestad.Domain.ISupportElementManager','Haestad.Domain.IManager','Haestad.Domain.IElement') {
    $t = $d.GetType($n); if (-not $t) { "!! $n"; continue }; "== $n"; Sig $t
}
foreach ($n in 'Haestad.Support.Support.IField','Haestad.Support.Support.IEditField','Haestad.Support.Support.ICollectionField','Haestad.Support.Support.IEditCollectionField','Haestad.Support.Support.ICollectionFieldListManager','Haestad.Support.Support.ICollectionFieldListManagerEx') {
    $t = $s.GetType($n); if (-not $t) { "!! $n"; continue }; "== $n"; Sig $t
}
"== StandardAlternativeName constants"
$t = $d.GetType('Haestad.Domain.StandardAlternativeName'); if ($t) { $t.GetFields() | % { "  " + $_.Name + " = " + $_.GetValue($null) } }
"== StandardCalculationOptionFieldName (first 80)"
$t = $d.GetType('Haestad.Domain.StandardCalculationOptionFieldName'); if ($t) { $t.GetFields() | select -First 80 | % { "  " + $_.Name + " = " + $_.GetValue($null) } }
