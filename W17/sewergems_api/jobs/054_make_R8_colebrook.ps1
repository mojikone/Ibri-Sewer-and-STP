. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# R8: R4 (the loads every option builds on) with Colebrook-White friction for gravity pipes (engineer, 2026-10-01).
$src = 'C:\IbriWork\W17\IBRI_W17_R4.stsw'; $dst = 'C:\IbriWork\W17\IBRI_W17_R8.stsw'
$out = '\\VBOXSVR\VBOX\bridge\out\r8'; New-Item -ItemType Directory -Force $out | Out-Null
$log = New-Object IO.StringWriter
Get-ChildItem 'C:\IbriWork\W17' -Filter 'IBRI_W17_R8.stsw*' | Remove-Item -Force
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open($src)
  $m.SaveAs($dst)
  $log.WriteLine('== before: 2030 analysis on the modeller''s pipes (Manning)')
  [Scen]::Run($m, 279763, $log); [Scen]::Export($m, $out, 'manning_2030', $log)
  $log.WriteLine('== Colebrook-White, ks 1.5 mm, nu 1.141e-6 m2/s')
  [Friction]::CalcOptions($m, [int[]]@(31, 279786), 1.141e-6, $log)
  [Friction]::ConduitRoughness($m, 6, 1.5, $log)
  [Friction]::CatalogueRoughness($m, 1.5, $log)
  $log.WriteLine('== after: the same 2030 analysis')
  [Scen]::Run($m, 279763, $log); [Scen]::Export($m, $out, 'colebrook_2030', $log)
  $m.Save(); $log.WriteLine('  saved ' + $dst)
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
[IO.File]::WriteAllText("$out\log.txt", $log.ToString())
$log.ToString()
