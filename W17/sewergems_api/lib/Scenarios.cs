using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;
using OpenFlows.StormSewer.Domain.ModelingElements;

public static class Scen
{
    public const double M3D_PER_CFS = 2446.575545;
    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    // Manning's n of every size in the conduit catalogue (the design gives each pipe it sizes the catalogue value).
    public static void SetCatalogueN(IStormSewerModel m, double n, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("CatalogConduit");
        var f = (IEditField)dds.FieldManager.SupportElementField("ClassSizeCollection", st.Id);
        foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
        {
            var lm = f.GetValue(el.Id);
            var clm = (ICollectionFieldListManager)lm;
            var items = View(lm).Cast<System.Data.DataRowView>().Select(r => Convert.ToInt32(r["ItemID"])).ToList();
            foreach (int it in items) ((IEditField)clm.Field("ClassSizeCollection_ManningsN")).SetValue(it, n);
            f.SetValue(el.Id, lm);
            ((IEditField)dds.FieldManager.SupportElementField("ConstantRoughnessType_ManningsN", st.Id)).SetValue(el.Id, n);
            log.WriteLine("  catalogue '{0}': Manning n = {1} on {2} sizes", el.Label, n, items.Count);
        }
    }

    public static int ChildAlternative(IStormSewerModel m, string altType, int parentId, string label, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var am = dds.AlternativeManager(dds.DomainDataSetType().AlternativeType(altType).Id);
        var existing = am.Elements().Cast<IAlternative>().FirstOrDefault(a => a.Label == label && a.ParentID == parentId);
        if (existing != null) { log.WriteLine("  {0} '{1}' exists ({2})", altType, label, existing.Id); return existing.Id; }
        int id = am.Add(parentId);
        ((IAlternative)am.Element(id)).Label = label;
        log.WriteLine("  {0} child '{1}' = {2} under {3}", altType, label, id, parentId);
        return id;
    }

    // A child scenario that inherits everything, then takes the given alternatives and calculation options locally.
    public static int ChildScenario(IStormSewerModel m, int parentScenarioId, string label, IDictionary<string, int> alts, int calcOptionsId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var sm = dds.ScenarioManager;
        var existing = sm.Elements().Cast<IScenario>().FirstOrDefault(s => s.Label == label);
        int id;
        if (existing != null) id = existing.Id;
        else
        {
            var s = m.Scenarios.Create();
            s.Label = label;
            s.ParentScenario = m.Scenarios.Element(parentScenarioId);
            id = s.Id;
        }
        var hs = (IScenario)sm.Element(id);
        var dst = dds.DomainDataSetType();
        // local, not inherited: an inherited value silently follows any later change to the parent
        foreach (var kv in alts) { hs.MakeAlternativeLocal(dst.AlternativeType(kv.Key).Id); hs.AlternativeID(kv.Key, kv.Value); }
        if (calcOptionsId > 0) { hs.MakeCalculationOptionsLocal("DelawareProductEngine"); hs.CalculationOptionsID("DelawareProductEngine", calcOptionsId); }
        log.WriteLine("  scenario '{0}' = {1} (parent {2}); {3}; calc {4} (local {5})", label, id, hs.ParentID,
            string.Join(", ", alts.Select(kv => kv.Key + "=" + hs.AlternativeID(kv.Key) + (hs.IsAlternativeLocal(dst.AlternativeType(kv.Key).Id) ? " local" : " INHERITED"))),
            hs.CalculationOptionsID("DelawareProductEngine"), hs.IsCalculationOptionsLocal("DelawareProductEngine"));
        return id;
    }

    // Transfer rows (pattern loads, not peaked) from a CSV: year,source,receiver_id,receiver_label,flow_m3d.
    public static void AddTransfers(IStormSewerModel m, IDictionary<string, int> sanitaryByYear, string csv, TextWriter log)
    {
        int n = 0;
        foreach (var line in File.ReadAllLines(csv).Skip(1))
        {
            var p = line.Split(',');
            string year = p[0], src = p[1]; int mh = int.Parse(p[2]); double q = double.Parse(p[4], System.Globalization.CultureInfo.InvariantCulture);
            Transfer.AddPatternLoad(m, sanitaryByYear[year], mh, q / M3D_PER_CFS, TextWriter.Null);
            n++;
        }
        log.WriteLine("  {0} transfer rows written", n);
    }

    public static void Run(IStormSewerModel m, int scenarioId, TextWriter log)
    {
        var s = m.Scenarios.Element(scenarioId);
        m.SetActiveScenario(s);
        var t0 = DateTime.Now;
        try { s.Run(); }
        catch (Exception ex)
        {
            var notes = new List<string>();
            var p = ex.GetType().GetProperty("UserNotifications");
            if (p != null) foreach (var it in (IEnumerable)p.GetValue(ex, null)) notes.Add(Convert.ToString(it));
            var g = notes.GroupBy(x => x).Select(x => x.Key + " x" + x.Count());
            log.WriteLine("  '{0}' run raised {1}: {2}", s.Label, ex.GetType().Name, string.Join("; ", g));
        }
        log.WriteLine("  '{0}' ran in {1:n0} s, results: {2}", s.Label, (DateTime.Now - t0).TotalSeconds, s.HasResults);
    }

    // Catalogue size of every conduit in the active scenario (to detect design changes).
    public static Dictionary<int, string> Sizes(IStormSewerModel m)
    {
        return m.Network.Conduits.Elements().ToDictionary(c => c.Id, c => c.Input.Size.ToString().ToLowerInvariant());
    }

    // Design the scenario repeatedly until no catalogue size changes (or maxRuns).
    public static void DesignUntilStable(IStormSewerModel m, int scenarioId, int maxRuns, TextWriter log)
    {
        m.SetActiveScenario(m.Scenarios.Element(scenarioId));
        var prev = Sizes(m);
        for (int k = 1; k <= maxRuns; k++)
        {
            Run(m, scenarioId, log);
            var now = Sizes(m);
            int changed = now.Count(kv => prev[kv.Key] != kv.Value);
            log.WriteLine("  design pass {0}: {1} pipe sizes changed", k, changed);
            if (changed == 0) break;
            prev = now;
        }
    }

    // Pipe and manhole table of the active scenario (inputs as designed, results of the last run).
    public static void Export(IStormSewerModel m, string dir, string tag, TextWriter log)
    {
        Directory.CreateDirectory(dir);
        var ci = System.Globalization.CultureInfo.InvariantCulture;
        var cat = SizeCheck.Catalogue(m);   // catalogue pipes: the size reference holds the real size; the diameter field can be stale
        using (var w = new StreamWriter(Path.Combine(dir, "conduits_" + tag + ".csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,start,stop,active,length_m,diameter_mm,size_label,start_inv,stop_inv,flow_m3d,velocity_ms,depth_in_m,depth_out_m");
            foreach (var c in m.Network.Conduits.Elements())
            {
                var i = c.Input;
                Func<double?, string> f = v => v.HasValue ? v.Value.ToString("R", ci) : "";
                Tuple<string, double> sz; cat.TryGetValue(i.Size.ToString().ToLowerInvariant(), out sz);
                w.WriteLine(string.Join(",", c.Id, c.Label, i.StartNode.Id, i.StopNode.Id, i.IsActive, i.Length.ToString("R", ci), (sz != null ? sz.Item2 : i.ConduitDiameter).ToString("R", ci),
                    "\"" + (sz != null ? sz.Item1 : i.ConduitShapeLabel) + "\"", i.StartInvert.ToString("R", ci), i.StopInvert.ToString("R", ci),
                    f(c.Results.Flow()), f(c.Results.Velocity()), f(c.Results.DepthIn()), f(c.Results.DepthOut())));
            }
        }
        using (var w = new StreamWriter(Path.Combine(dir, "manholes_" + tag + ".csv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("id,label,active,x,y,ground,rim,invert,diameter_m");
            foreach (var n in m.Network.Manholes.Elements())
            {
                var i = n.Input; var p = i.GetPoint();
                w.WriteLine(string.Join(",", n.Id, n.Label, i.IsActive, p.X.ToString("R", ci), p.Y.ToString("R", ci), i.GroundElevation.ToString("R", ci),
                    i.RimElevation.ToString("R", ci), i.InvertElevation.ToString("R", ci), i.Diameter.ToString("R", ci)));
            }
            foreach (var n in m.Network.Outfalls.Elements())
            {
                var i = n.Input; var p = i.GetPoint();
                w.WriteLine(string.Join(",", n.Id, n.Label, i.IsActive, p.X.ToString("R", ci), p.Y.ToString("R", ci), i.GroundElevation.ToString("R", ci),
                    i.RimElevation.ToString("R", ci), i.InvertElevation.ToString("R", ci), ""));
            }
        }
        var d = Transfer.OutfallFlows(m);
        File.WriteAllText(Path.Combine(dir, "outfalls_" + tag + ".csv"), string.Join("\n", d.Select(kv => kv.Key + "," + kv.Value.ToString("R", ci))));
        log.WriteLine("  exported '{0}'", tag);
    }
}
