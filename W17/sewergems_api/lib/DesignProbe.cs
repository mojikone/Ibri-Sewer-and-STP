using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class DesignProbe
{
    static string Hist(IDictionary vals, int top)
    {
        var h = new Dictionary<string, int>();
        foreach (DictionaryEntry e in vals) { var k = Convert.ToString(e.Value, System.Globalization.CultureInfo.InvariantCulture); h[k] = h.ContainsKey(k) ? h[k] + 1 : 1; }
        return string.Join("; ", h.OrderByDescending(kv => kv.Value).Take(top).Select(kv => "'" + kv.Key + "' x" + kv.Value)) + (h.Count > top ? " (+" + (h.Count - top) + " more)" : "");
    }

    public static void Run(IStormSewerModel m, TextWriter log)
    {
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType(); var fm = dds.FieldManager;
        foreach (var atName in new[] { "Design", "InfiltrationAndInflow" })
        {
            var at = dst.AlternativeType(atName);
            var am = dds.AlternativeManager(at.Id);
            int baseId = am.BaseElements().Cast<IModelingElement>().First().Id;
            log.WriteLine("== {0} alternative {1}: system record fields", atName, baseId);
            foreach (IField f in fm.SystemRecordFields(at.Id))
            {
                object v; try { v = am.SystemRecordField(f.Name).GetValue(baseId); } catch (Exception ex) { v = "<" + ex.GetType().Name + ">"; }
                log.WriteLine("   {0} = {1}", f.Name, v);
            }
            foreach (int et in new[] { 1, 3, 5 })
            {
                log.WriteLine("== {0} fields on element type {1}", atName, et);
                FieldCollection fc; try { fc = fm.AlternativeFields(at.Id, et, baseId); } catch { continue; }
                foreach (IField f in fc)
                {
                    if (f.FieldDataType == FieldDataType.Collection || f.FieldDataType == FieldDataType.LongBinary) { log.WriteLine("   {0} (collection)", f.Name); continue; }
                    try { log.WriteLine("   {0}: {1}", f.Name, Hist(f.GetValues(), 4)); } catch (Exception ex) { log.WriteLine("   {0}: <{1}>", f.Name, ex.GetType().Name); }
                }
            }
        }
        log.WriteLine("== conduit catalogue");
        var cst = dst.SupportElementType("CatalogConduit");
        foreach (IModelingElement el in dds.SupportElementManager(cst.Id).Elements())
            foreach (IField f in fm.SupportElementFields(cst.Id))
            {
                object v; try { v = f.GetValue(el.Id); } catch { v = "?"; }
                log.WriteLine("   {0} | {1} = {2}", el.Label, f.Name, v);
                if (v != null && v.GetType().GetProperty("DataView") != null) Probe.DumpTable(v, log);
            }
        log.WriteLine("== physical conduit fields that matter for design (2070 base physical 6)");
        int pt = dst.AlternativeType("Physical").Id;
        foreach (IField f in fm.AlternativeFields(pt, 3, 6))
        {
            string n = f.Name.ToLowerInvariant();
            if (!(n.Contains("material") || n.Contains("manning") || n.Contains("rough") || n.Contains("diameter") || n.Contains("catalog") || n.Contains("size") || n.Contains("shape"))) continue;
            try { log.WriteLine("   {0}: {1}", f.Name, Hist(f.GetValues(), 6)); } catch { }
        }
    }
}
