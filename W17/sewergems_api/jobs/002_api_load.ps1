# Load the OpenFlows API assemblies (no model opened, no compute) and list the sewer entry points.
$OutputEncoding = [Console]::OutputEncoding = [Text.Encoding]::UTF8
$bin = 'C:\Program Files (x86)\Bentley\SewerGEMS\x64'
Set-Location $bin
[AppDomain]::CurrentDomain.add_AssemblyResolve({ param($s,$e)
    $p = Join-Path 'C:\Program Files (x86)\Bentley\SewerGEMS\x64' (($e.Name -split ',')[0] + '.dll')
    if (Test-Path $p) { [Reflection.Assembly]::LoadFrom($p) } })
foreach ($n in 'OpenFlows.dll','OpenFlows.StormSewer.dll') {
    "== $n"
    try {
        $a = [Reflection.Assembly]::LoadFrom((Join-Path $bin $n))
        "loaded: " + $a.FullName + "  runtime " + $a.ImageRuntimeVersion
        try { $types = $a.GetExportedTypes() } catch [Reflection.ReflectionTypeLoadException] { $types = $_.Exception.Types | Where-Object { $_ } }
        "exported types: " + $types.Count
        $types | Where-Object { $_.Name -match '^(I?StormSewerModel|I?SewerModel|OpenFlowsStormSewer|OpenFlowsSewer|ApplicationManager|.*Session|.*ModelOpen.*)$' -or ($_.IsClass -and $_.IsAbstract -and $_.IsSealed) } |
            Select-Object -First 40 | ForEach-Object { "  " + $_.FullName }
    } catch { "FAILED: $($_.Exception.Message)" }
}
