# File-drop bridge: runs every *.ps1 placed in .\jobs, writes its output to .\out,
# then moves the job to .\done. No network is used. Close this window to stop it.
$root = $PSScriptRoot
foreach ($d in 'jobs','out','done') { New-Item -ItemType Directory -Force (Join-Path $root $d) | Out-Null }
Write-Host "Bridge watching $root\jobs  (close this window to stop)"
while ($true) {
    Set-Content -Path (Join-Path $root 'out\_alive.txt') -Value (Get-Date -Format o)
    Get-ChildItem (Join-Path $root 'jobs') -Filter *.ps1 -ErrorAction SilentlyContinue | Sort-Object Name | ForEach-Object {
        $job = $_
        $log = Join-Path $root ("out\" + $job.BaseName + ".txt")
        Write-Host ("[{0}] running {1}" -f (Get-Date -Format T), $job.Name)
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $job.FullName *> $log
        Add-Content -Path $log -Value ("`n__EXIT__ " + $LASTEXITCODE)
        Move-Item -Force $job.FullName (Join-Path $root ("done\" + $job.Name))
    }
    Start-Sleep -Seconds 2
}
