using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class ResultFields
{
    // List conduit result fields of the GVF-convex engine, then export the flow-related ones for the given conduits.
    public static void Export(IStormSewerModel m, int scenarioId, IList<int> conduitIds, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var sm = dds.ScenarioManager;
        var scen = (IScenario)sm.Element(scenarioId);
        string eng = "DelawareProductEngine";
        try { eng = scen.GetActiveNumericalEngineTypeName("StormSewerResultRecordType"); } catch { }
        if (string.IsNullOrEmpty(eng)) eng = "DelawareProductEngine";
        var conduitMgr = dds.DomainElementManager(3);
        log.WriteLine("engine " + eng + "; record types: " + string.Join(",", conduitMgr.DomainElementType().SupportedResultRecordTypeNames().Cast<string>()));
        var picked = new List<IField>();
        foreach (string rrt in conduitMgr.DomainElementType().SupportedResultRecordTypeNames())
        {
            FieldCollection fc;
            try { fc = dds.FieldManager.ResultFields(eng, rrt, 3); } catch { continue; }
            foreach (IField f in fc)
            {
                log.WriteLine("  [{0}] {1} | {2}", rrt, f.Name, f.Label);
                string s = (f.Name + " " + f.Label).ToLowerInvariant();
                if (s.Contains("flow") || s.Contains("factor") || s.Contains("load") || s.Contains("population")) picked.Add(f);
            }
        }
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            w.WriteLine("id," + string.Join(",", picked.Select(f => f.Name)));
            foreach (int id in conduitIds)
            {
                var vals = new List<string>();
                foreach (var f in picked)
                {
                    object v;
                    try
                    {
                        var rf = f as IResultTimeVariantField;
                        if (rf != null) v = rf.GetValue(id, scenarioId, 0); else v = f.GetValue(id);
                    }
                    catch (Exception ex) { v = "ERR:" + ex.GetType().Name; }
                    vals.Add(Convert.ToString(v, System.Globalization.CultureInfo.InvariantCulture));
                }
                w.WriteLine(id + "," + string.Join(",", vals));
            }
        }
    }
}
