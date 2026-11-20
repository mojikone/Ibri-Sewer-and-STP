using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class DesignProbe2
{
    public static void Run(IStormSewerModel m, TextWriter log)
    {
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType(); var fm = dds.FieldManager;
        var dt = dst.AlternativeType("Design"); var dam = dds.AlternativeManager(dt.Id);
        foreach (var t in new[] { "SystemSlopeVersusRiseTable", "SystemPercentFullVersusRiseTable" })
        {
            log.WriteLine("== " + t);
            var v = dam.SystemRecordField(t).GetValue(17);
            Probe.DumpTable(v, log);
        }
        log.WriteLine("== Manning n by diameter (physical 6)");
        int pt = dst.AlternativeType("Physical").Id;
        var n = fm.AlternativeField("Physical_ManningsN", pt, 3, 6).GetValues();
        var d = fm.AlternativeField("ConduitDiameter", pt, 3, 6).GetValues();
        var lab = dds.DomainElementManager(3).ModelingElementField("Label").GetValues();
        var g = new Dictionary<string, int>();
        foreach (DictionaryEntry e in n) { string k = (Convert.ToDouble(d[e.Key]) * 304.8).ToString("0.0") + " mm | n=" + e.Value; g[k] = g.ContainsKey(k) ? g[k] + 1 : 1; }
        foreach (var kv in g.OrderBy(kv => kv.Key)) log.WriteLine("   {0} : {1}", kv.Key, kv.Value);
        var subs = new Dictionary<string, int>();
        foreach (DictionaryEntry e in n) if (Convert.ToDouble(e.Value) < 0.012) { string s = Convert.ToString(lab[e.Key]).Split('-')[0]; subs[s] = subs.ContainsKey(s) ? subs[s] + 1 : 1; }
        log.WriteLine("   pipes with n < 0.012 by subnetwork: " + string.Join(", ", subs.OrderByDescending(kv => kv.Value).Select(kv => kv.Key + " " + kv.Value)));
        log.WriteLine("== inflow rows on outfalls (Base I&I)");
        int it = dst.AlternativeType("InfiltrationAndInflow").Id;
        var cnt = fm.AlternativeField("InflowListCount", it, 5, 11).GetValues();
        var col = fm.AlternativeField("InflowList", it, 5, 11);
        var olab = dds.DomainElementManager(5).ModelingElementField("Label").GetValues();
        foreach (DictionaryEntry e in cnt) if (Convert.ToInt32(e.Value ?? 0) > 0) { log.WriteLine("   outfall " + olab[e.Key]); Probe.DumpTable(col.GetValue((int)e.Key), log); }
    }
}
