# 1) Show the OpenFlowsStormSewer entry-point methods (no guessing the API).
# 2) Make a working copy of the model inside the VM, so the shared original is never opened.
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
$a = [Reflection.Assembly]::LoadFrom((Join-Path $bin 'OpenFlows.StormSewer.dll'))
$t = $a.GetType('OpenFlows.StormSewer.OpenFlowsStormSewer')
"== OpenFlowsStormSewer static methods"
$t.GetMethods([Reflection.BindingFlags]'Public,Static') | ForEach-Object {
    "  " + $_.ReturnType.Name + " " + $_.Name + "(" + (($_.GetParameters() | ForEach-Object { $_.ParameterType.Name + " " + $_.Name }) -join ", ") + ")" }
"== enums used by StartSession"
$t.GetMethods() | Where-Object Name -eq 'StartSession' | ForEach-Object { $_.GetParameters() } | ForEach-Object {
    if ($_.ParameterType.IsEnum) { "  " + $_.ParameterType.FullName + ": " + ([Enum]::GetNames($_.ParameterType) -join ', ') } }

"== working copy"
$src = '\\VBOXSVR\Win10_shared_folder\IBRI Sewer\13 IBRI_29092026 12M(7.12 PM )'
$dst = 'C:\IbriWork\M13'
New-Item -ItemType Directory -Force $dst | Out-Null
foreach ($f in 'IBRI_3_9_2026_12M.stsw','IBRI_3_9_2026_12M.stsw.sqlite','IBRI_3_9_2026_12M.stsw.dwh','IBRI_3_9_2026_12M.stsw.profiles.dwh') {
    Copy-Item -LiteralPath (Join-Path $src $f) -Destination $dst -Force
}
Get-ChildItem $dst | ForEach-Object { "  {0,12}  {1}" -f $_.Length, $_.Name }
