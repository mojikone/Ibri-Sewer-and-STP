# Host-side compile check of lib\*.cs against the SewerGEMS libraries copied to refs\ (nothing is executed).
$refsDir = Join-Path $PSScriptRoot 'refs'
$refs = Get-ChildItem $refsDir -Filter *.dll | Where-Object { $_.Name -match '^(OpenFlows|Haestad\.(Domain|Support|Delaware|Framework|Calculations)|Haestad\.Domain\.ModelingObjects)' } | ForEach-Object { $_.FullName }
$refs = @($refs | Where-Object { try { [void][Reflection.AssemblyName]::GetAssemblyName($_); $true } catch { $false } })
$refs += 'System.dll','System.Data.dll','System.Xml.dll','System.Core.dll','Microsoft.CSharp.dll'
$lines = Get-ChildItem (Join-Path $PSScriptRoot 'lib\*.cs') | ForEach-Object { Get-Content $_.FullName }
$usings = $lines | Where-Object { $_ -match '^using [\w\.]+;' } | Sort-Object -Unique
$body = $lines | Where-Object { $_ -notmatch '^using [\w\.]+;' }
$cp = New-Object System.CodeDom.Compiler.CompilerParameters
$cp.GenerateInMemory = $false; $cp.GenerateExecutable = $false
$cp.OutputAssembly = Join-Path $env:TEMP ("ibri_check_" + [guid]::NewGuid().ToString('N') + ".dll")
$refs | ForEach-Object { [void]$cp.ReferencedAssemblies.Add($_) }
$prov = New-Object Microsoft.CSharp.CSharpCodeProvider
$r = $prov.CompileAssemblyFromSource($cp, (($usings + $body) -join "`n"))
if ($r.Errors.HasErrors) { $r.Errors | Where-Object { -not $_.IsWarning } | ForEach-Object { "L{0}: {1}" -f ($_.Line - $usings.Count), $_.ErrorText }; exit 1 } else { "compile OK" }
