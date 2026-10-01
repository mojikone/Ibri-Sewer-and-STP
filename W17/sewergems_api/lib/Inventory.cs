using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer;
using OpenFlows.StormSewer.Domain;

public static class Inventory
{
    static string Q(object o) { var s = o == null ? "" : Convert.ToString(o, System.Globalization.CultureInfo.InvariantCulture); return s.Contains(",") || s.Contains("\"") ? "\"" + s.Replace("\"", "\"\"") + "\"" : s; }

    public static void Run(IStormSewerModel m, string outDir, TextWriter log)
    {
        Directory.CreateDirectory(outDir);
        var dds = m.DomainDataSet;
        var dst = dds.DomainDataSetType();

        log.WriteLine("== alternative types and alternatives");
        foreach (IAlternativeType at in dst.AlternativeTypes())
        {
            IAlternativeManager am;
            try { am = dds.AlternativeManager(at.Id); } catch { continue; }
            log.WriteLine("[{0}] {1} / {2}  count={3}", at.Id, at.Name, at.Label, am.Count);
            foreach (IAlternative a in am.Elements())
                log.WriteLine("      {0,8}  parent={1,8}  {2}", a.Id, a.ParentID, a.Label);
        }

        log.WriteLine("== numerical engines and calculation options");
        var sm = dds.ScenarioManager;
        foreach (INumericalEngineType ne in dst.NumericalEngineTypes())
        {
            try
            {
                var com = sm.CalculationOptionsManager(ne.Name);
                log.WriteLine("[{0}] {1}  options={2}", ne.Id, ne.Name, com.Count);
                foreach (IModelingElement co in com.Elements()) log.WriteLine("      {0,8}  {1}", co.Id, co.Label);
            }
            catch (Exception ex) { log.WriteLine("[{0}] {1}  ({2})", ne.Id, ne.Name, ex.GetType().Name); }
        }

        log.WriteLine("== scenarios");
        var alts = dst.AlternativeTypes().Cast<IAlternativeType>().ToList();
        foreach (IScenario s in sm.Elements())
        {
            var sb = new StringBuilder();
            foreach (var at in alts) { try { sb.AppendFormat(" {0}={1}", at.Name, s.AlternativeID(at.Id)); } catch { } }
            string eng = ""; try { eng = s.GetActiveNumericalEngineTypeName("StormSewerResultRecordType"); } catch { }
            log.WriteLine("{0,8} parent={1,8} '{2}' engine={3}", s.Id, s.ParentID, s.Label, eng);
            log.WriteLine("        " + sb);
            foreach (INumericalEngineType ne in dst.NumericalEngineTypes())
                try { log.WriteLine("        calc[{0}]={1}", ne.Name, s.CalculationOptionsID(ne.Name)); } catch { }
        }

        // topology
        using (var w = new StreamWriter(Path.Combine(outDir, "nodes.csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,type,x,y,active");
            foreach (var n in m.Network.Manholes.Elements()) { var p = n.Input.GetPoint(); w.WriteLine(string.Join(",", n.Id, Q(n.Label), "MH", Q(p.X), Q(p.Y), n.Input.IsActive)); }
            foreach (var n in m.Network.Outfalls.Elements()) { var p = n.Input.GetPoint(); w.WriteLine(string.Join(",", n.Id, Q(n.Label), "OF", Q(p.X), Q(p.Y), n.Input.IsActive)); }
            foreach (var n in m.Network.WetWells.Elements()) { var p = n.Input.GetPoint(); w.WriteLine(string.Join(",", n.Id, Q(n.Label), "WW", Q(p.X), Q(p.Y), n.Input.IsActive)); }
            foreach (var n in m.Network.Pumps.Elements()) { var p = n.Input.GetPoint(); w.WriteLine(string.Join(",", n.Id, Q(n.Label), "PMP", Q(p.X), Q(p.Y), n.Input.IsActive)); }
            foreach (var n in m.Network.PressureJunctions.Elements()) { var p = n.Input.GetPoint(); w.WriteLine(string.Join(",", n.Id, Q(n.Label), "PJ", Q(p.X), Q(p.Y), n.Input.IsActive)); }
        }
        using (var w = new StreamWriter(Path.Combine(outDir, "links.csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,type,start,stop,active,length,diameter,start_inv,stop_inv");
            foreach (var c in m.Network.Conduits.Elements())
                w.WriteLine(string.Join(",", c.Id, Q(c.Label), "CO", c.Input.StartNode.Id, c.Input.StopNode.Id, c.Input.IsActive, Q(c.Input.Length), Q(c.Input.ConduitDiameter), Q(c.Input.StartInvert), Q(c.Input.StopInvert)));
            foreach (var c in m.Network.PressurePipes.Elements())
                w.WriteLine(string.Join(",", c.Id, Q(c.Label), "PP", c.Input.StartNode.Id, c.Input.StopNode.Id, c.Input.IsActive, "", "", "", ""));
        }

        // fields per manhole in the loading-related alternative types
        log.WriteLine("== manhole fields by alternative type");
        log.WriteLine("domain element types: " + string.Join(" | ", dst.DomainElementTypes().Cast<IDomainElementType>().Select(t => t.Id + ":" + t.Name)));
        var mhType = dst.DomainElementTypes().Cast<IDomainElementType>().First(t => t.Name.IndexOf("Manhole", StringComparison.OrdinalIgnoreCase) >= 0);
        foreach (var at in alts)
        {
            try
            {
                var fts = at.FieldTypes(mhType.Id);
                if (fts.Count == 0) continue;
                log.WriteLine("[{0}] {1}: {2}", at.Id, at.Name, string.Join(" | ", fts.Cast<IFieldType>().Select(f => f.Name + ":" + f.FieldDataType().ToString())));
            }
            catch { }
        }

        log.WriteLine("== support element types");
        foreach (ISupportElementType st in dst.SupportElementTypes())
        {
            int cnt = -1; try { cnt = dds.SupportElementManager(st.Id).Count; } catch { }
            if (cnt > 0) log.WriteLine("[{0}] {1}  count={2}", st.Id, st.Name, cnt);
        }
    }
}
