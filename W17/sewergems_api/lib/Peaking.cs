using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Peaking
{
    // Sum of sanitary rows per manhole for one sanitary-loading alternative, split by load definition.
    public static void ExportBaseLoads(IStormSewerModel m, int sanAltId, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int sanT = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var f = dds.FieldManager.AlternativeField("SanitaryLoads", sanT, 1, sanAltId);
        var cnt = dds.FieldManager.AlternativeField("SanitaryLoadsCount", sanT, 1, sanAltId).GetValues();
        var defs = new Dictionary<int, int>();
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,base_flow_m3s,rows,defs");
            foreach (DictionaryEntry e in cnt)
            {
                if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
                int id = (int)e.Key;
                var lm = f.GetValue(id);
                var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
                double q = 0; int rows = 0; var ds = new List<string>();
                foreach (System.Data.DataRowView r in dv)
                {
                    int d = Convert.ToInt32(r["LoadDefinition"]);
                    defs[d] = defs.ContainsKey(d) ? defs[d] + 1 : 1;
                    if (r["SanitaryPatternLoadType_SanitaryBaseFlow"] != DBNull.Value) q += Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]);
                    rows++; ds.Add(d.ToString());
                }
                w.WriteLine("{0},{1},{2},{3},{4}", id, "", q.ToString("R"), rows, string.Join("/", ds));
            }
        }
        log.WriteLine("  load definitions in alt {0}: {1}", sanAltId, string.Join(", ", defs.Select(kv => kv.Key + "x" + kv.Value)));
    }

    public static void RunAndExport(IStormSewerModel m, int scenarioId, string csv, TextWriter log)
    {
        var s = m.Scenarios.Element(scenarioId);
        m.SetActiveScenario(s);
        var t0 = DateTime.Now;
        try { s.Run(); }
        catch (Exception ex)
        {
            log.WriteLine("  run raised " + ex.GetType().Name + ": " + ex.Message);
            foreach (var pi in ex.GetType().GetProperties()) { try { var v = pi.GetValue(ex, null); var en = v as IEnumerable; if (en != null && !(v is string)) { int k = 0; foreach (var it in en) { log.WriteLine("    " + pi.Name + ": " + it); if (++k > 20) break; } } } catch { } }
        }
        log.WriteLine("  ran '{0}' in {1:n0} s; has results: {2}", s.Label, (DateTime.Now - t0).TotalSeconds, s.HasResults);
        var notes = s.GetRunUserNotifications();
        log.WriteLine("  notifications: " + (notes == null ? 0 : notes.Length));
        if (notes != null) foreach (var n in notes.Take(15)) log.WriteLine("    " + n);
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,start,stop,flow_m3s,velocity,diameter");
            foreach (var c in m.Network.Conduits.Elements())
            {
                var q = c.Results.Flow(); var v = c.Results.Velocity();
                w.WriteLine("{0},{1},{2},{3},{4},{5},{6}", c.Id, c.Label, c.Input.StartNode.Id, c.Input.StopNode.Id,
                    q.HasValue ? q.Value.ToString("R") : "", v.HasValue ? v.Value.ToString("R") : "", c.Input.ConduitDiameter);
            }
        }
    }
}
