using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using System.Reflection;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Probe
{
    public static void Dump(object v, TextWriter log, string indent, int depth)
    {
        if (v == null) { log.WriteLine(indent + "null"); return; }
        var t = v.GetType();
        log.WriteLine(indent + "type " + t.FullName + "  ifaces: " + string.Join(",", t.GetInterfaces().Select(i => i.Name)));
        if (depth <= 0) return;
        foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            if (p.GetIndexParameters().Length > 0) continue;
            object pv; try { pv = p.GetValue(v, null); } catch (Exception ex) { pv = "<" + ex.GetType().Name + ">"; }
            log.WriteLine(indent + "  ." + p.Name + " = " + pv);
        }
    }

    public static void DumpTable(object listManager, TextWriter log)
    {
        var dv = listManager.GetType().GetProperty("DataView").GetValue(listManager, null) as System.Data.DataView;
        if (dv == null) { log.WriteLine("      (no DataView)"); return; }
        log.WriteLine("      columns: " + string.Join(" | ", dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName + ":" + c.DataType.Name)));
        int i = 0;
        foreach (System.Data.DataRowView r in dv)
        {
            log.WriteLine("      row: " + string.Join(" | ", dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName + "=" + r[c.ColumnName])));
            if (++i >= 8) break;
        }
    }

    public static void Run(IStormSewerModel m, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var fm = dds.FieldManager;
        var dst = dds.DomainDataSetType();
        int mhT = 1;
        int sanT = dst.AlternativeType("SanitaryLoading").Id;
        int sfT = dst.AlternativeType("SystemFlows").Id;
        var mhIds = dds.DomainElementManager(mhT).ElementIDs();

        foreach (int altId in new[] { 14, 279769, 279774 })
        {
            var f = fm.AlternativeField("SanitaryLoadsCount", sanT, mhT, altId);
            var vals = f.GetValues();
            int n = 0, rows = 0;
            foreach (DictionaryEntry e in vals) { int c = Convert.ToInt32(e.Value ?? 0); if (c > 0) { n++; rows += c; } }
            log.WriteLine("sanitary alt {0}: manholes with loads={1} rows={2}", altId, n, rows);
        }
        foreach (int altId in new[] { 18, 279775, 279780 })
        {
            var f = fm.AlternativeField("SystemFlows_KnownFlow", sfT, mhT, altId);
            int n = 0; foreach (DictionaryEntry e in f.GetValues()) if (e.Value != null && !(e.Value is DBNull)) n++;
            log.WriteLine("system flows alt {0}: manholes with known flow={1}", altId, n);
        }

        // one manhole with loads in 2070: inspect the collection value
        var cntF = fm.AlternativeField("SanitaryLoadsCount", sanT, mhT, 14);
        int sample = -1;
        foreach (DictionaryEntry e in cntF.GetValues()) if (Convert.ToInt32(e.Value ?? 0) > 0) { sample = (int)e.Key; break; }
        log.WriteLine("sample manhole " + sample + "");
        var colF = fm.AlternativeField("SanitaryLoads", sanT, mhT, 14);
        log.WriteLine("collection field object:"); Dump(colF, log, "  ", 1);
        var cv = colF.GetValue(sample);
        log.WriteLine("collection value:"); Dump(cv, log, "  ", 1);
        DumpTable(cv, log);
        // known flows actually set (finite, non-zero)
        foreach (int altId in new[] { 18, 279775, 279780 })
        {
            var f = fm.AlternativeField("SystemFlows_KnownFlow", sfT, mhT, altId);
            int n = 0; double sum = 0;
            foreach (DictionaryEntry e in f.GetValues()) { double d; if (e.Value != null && double.TryParse(Convert.ToString(e.Value), out d) && !double.IsNaN(d) && d != 0) { n++; sum += d; } }
            log.WriteLine("system flows alt {0}: non-zero known flows={1} sum={2}", altId, n, sum);
        }

        // extreme flow setup
        foreach (string sname in new[] { "ExtremeFlowSetup", "ExtremeFlowFactor", "UnitSanitaryLoad", "PatternSetup", "IdahoPattern" })
        {
            var st = dst.SupportElementType(sname);
            var sm = dds.SupportElementManager(st.Id);
            log.WriteLine("== support " + sname);
            foreach (IModelingElement el in sm.Elements())
            {
                log.WriteLine("  element " + el.Id + " '" + el.Label + "'");
                foreach (IField fld in fm.SupportElementFields(st.Id))
                {
                    object v; try { v = fld.GetValue(el.Id); } catch (Exception ex) { v = "<" + ex.GetType().Name + ">"; }
                    log.WriteLine("    " + fld.Name + " = " + v);
                    if (v != null && v.GetType().GetProperty("DataView") != null) DumpTable(v, log);
                }
            }
        }
    }
}
