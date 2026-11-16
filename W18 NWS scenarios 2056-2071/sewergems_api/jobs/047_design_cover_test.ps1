. \\VBOXSVR\VBOX\bridge\lib\load.ps1
# Why does the S1 design not upsize? Scratch copy of R5: notes on overloaded pipes, then the design with max cover relaxed.
$work = 'C:\IbriWork\scratch_design2'; New-Item -ItemType Directory -Force $work | Out-Null
Copy-Item 'C:\IbriWork\W17\IBRI_W17_R5.stsw', 'C:\IbriWork\W17\IBRI_W17_R5.stsw.sqlite' $work -Force
$log = New-Object IO.StringWriter
$watch = [string[]]@('O1-P2429', 'O1-P2440', 'O2-P1', 'O9-P1')
[void][OpenFlows.StormSewer.OpenFlowsStormSewer]::StartSession([OpenFlows.StormSewer.StormSewerProductLicenseType]::SewerGEMS)
try {
  $m = [OpenFlows.StormSewer.OpenFlowsStormSewer]::Open("$work\IBRI_W17_R5.stsw")
  $log.WriteLine('== design as set (max cover 12 m)')
  $d0 = [DesignTest]::Diameters($m)
  [Scen]::Run($m, 279800, $log); [DesignTest]::Notes($m, 279800, $watch, $log)
  $d1 = [DesignTest]::Diameters($m); $n = 0; foreach ($k in $d0.Keys) { if ([math]::Abs($d0[$k] - $d1[$k]) -gt 1e-6) { $n++ } }; $log.WriteLine("  diameters changed: $n")
  $log.WriteLine('== design with max cover 40 m (scratch only)')
  [DesignTest]::SetDesignSystem($m, 'Design_SystemMaxCover', 131.2335958, $log)
  [Scen]::Run($m, 279800, $log); [DesignTest]::Notes($m, 279800, $watch, $log)
  $d2 = [DesignTest]::Diameters($m); $n = 0; foreach ($k in $d0.Keys) { if ([math]::Abs($d0[$k] - $d2[$k]) -gt 1e-6) { $n++ } }; $log.WriteLine("  diameters changed: $n")
  $m.Close()
} catch { $log.WriteLine('FAILED: ' + $_.Exception.ToString()) } finally { [OpenFlows.StormSewer.OpenFlowsStormSewer]::EndSession() }
$log.ToString()
