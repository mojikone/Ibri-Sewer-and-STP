# Shared loader: resolves SewerGEMS assemblies and compiles the C# helpers in this folder.
$global:SG_BIN = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $global:SG_BIN
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
$refs = @()
foreach ($dll in Get-ChildItem $global:SG_BIN -Filter *.dll | Where-Object { $_.Name -match '^(OpenFlows|Haestad\.(Domain|Support|Delaware|Framework|Calculations)|Haestad\.Domain\.ModelingObjects)' }) {
    try { [void][Reflection.AssemblyName]::GetAssemblyName($dll.FullName); [void][Reflection.Assembly]::LoadFrom($dll.FullName); $refs += $dll.FullName } catch {}
}
$refs += 'System.dll','System.Data.dll','System.Xml.dll','System.Core.dll','Microsoft.CSharp.dll'
$lines = Get-ChildItem (Join-Path $PSScriptRoot '*.cs') | ForEach-Object { Get-Content $_.FullName }
$usings = $lines | Where-Object { $_ -match '^using [\w\.]+;' } | Sort-Object -Unique
$body = $lines | Where-Object { $_ -notmatch '^using [\w\.]+;' }
Add-Type -TypeDefinition (($usings + $body) -join "`n") -ReferencedAssemblies $refs -Language CSharp
