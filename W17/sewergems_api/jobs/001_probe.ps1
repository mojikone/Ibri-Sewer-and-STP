# Probe: environment, network state, SewerGEMS install and its .NET API libraries.
"== host"; $env:COMPUTERNAME; [Environment]::Is64BitProcess; $PSVersionTable.PSVersion.ToString()
"== network adapters"; Get-NetIPConfiguration | Format-Table InterfaceAlias,IPv4Address,IPv4DefaultGateway -AutoSize | Out-String
"== internet test (expect failure)"; try { (Test-NetConnection 8.8.8.8 -Port 53 -WarningAction SilentlyContinue).TcpTestSucceeded } catch { "error: $_" }
"== Bentley install folders"
$roots = @("$env:ProgramFiles\Bentley", "${env:ProgramFiles(x86)}\Bentley") | Where-Object { Test-Path $_ }
$roots | ForEach-Object { Get-ChildItem $_ -Directory | Select-Object -ExpandProperty FullName }
"== candidate API assemblies"
$roots | ForEach-Object {
    Get-ChildItem $_ -Recurse -Include 'OpenFlows*.dll','Haestad.Domain*.dll','Haestad.Support*.dll','Bentley.*Sewer*.dll','*SewerGEMS*.dll','*.exe' -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match 'OpenFlows|Sewer|Haestad\.(Domain|Support)\.dll' } |
        Select-Object FullName, @{n='Version';e={$_.VersionInfo.FileVersion}} | Format-Table -AutoSize | Out-String -Width 400
}
"== python in VM"; Get-Command python, py -ErrorAction SilentlyContinue | Select-Object Source
