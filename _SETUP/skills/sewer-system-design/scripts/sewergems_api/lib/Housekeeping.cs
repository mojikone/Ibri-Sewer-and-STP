using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Housekeeping
{
    static IDomainDataSet D(IStormSewerModel m) { return m.DomainDataSet; }
    static int AltType(IStormSewerModel m, string name) { return D(m).DomainDataSetType().AlternativeType(name).Id; }

    public static void RenameAlternative(IStormSewerModel m, string altType, int id, string label, TextWriter log)
    {
        var am = D(m).AlternativeManager(AltType(m, altType));
        var a = (IAlternative)am.Element(id);
        log.WriteLine("  {0} alternative {1}: '{2}' -> '{3}'", altType, id, a.Label, label);
        a.Label = label;
    }

    public static void RenameCalcOptions(IStormSewerModel m, string engine, int id, string label, TextWriter log)
    {
        var com = D(m).ScenarioManager.CalculationOptionsManager(engine);
        var e = com.Element(id);
        log.WriteLine("  calc options {0}/{1}: '{2}' -> '{3}'", engine, id, e.Label, label);
        e.Label = label;
    }

    public static void DeleteAlternativeIfUnused(IStormSewerModel m, string altType, int id, TextWriter log)
    {
        var am = D(m).AlternativeManager(AltType(m, altType));
        var a = (IAlternative)am.Element(id);
        var refs = a.ReferencedScenarios();
        if (refs.Count > 0) { log.WriteLine("  KEPT {0} alternative {1} '{2}': used by {3} scenario(s)", altType, id, a.Label, refs.Count); return; }
        log.WriteLine("  deleted {0} alternative {1} '{2}'", altType, id, a.Label);
        am.Delete(id);
    }

    // Point every scenario at the base System Flows alternative, clear its known flows, delete the children.
    public static void DropSystemFlows(IStormSewerModel m, TextWriter log)
    {
        var dds = D(m);
        int sfT = AltType(m, "SystemFlows");
        var am = dds.AlternativeManager(sfT);
        int baseId = am.BaseElements().Cast<IModelingElement>().First().Id;
        foreach (IScenario s in dds.ScenarioManager.Elements())
            if (s.AlternativeID(sfT) != baseId) { s.AlternativeID(sfT, baseId); log.WriteLine("  scenario '{0}' -> base system flows", s.Label); }
        foreach (IModelingElement a in am.Elements().Cast<IModelingElement>().ToList())
            if (a.Id != baseId) { log.WriteLine("  deleted system flows alternative {0} '{1}'", a.Id, a.Label); am.Delete(a.Id); }
        foreach (string et in new[] { "Manhole", "Outfall", "WetWell", "CatchBasin", "JunctionChamber" })
        {
            int etId;
            try { etId = dds.DomainDataSetType().DomainElementType(et).Id; } catch { continue; }
            IField f;
            try { f = dds.FieldManager.AlternativeField("SystemFlows_KnownFlow", sfT, etId, baseId); } catch { continue; }
            var ef = (IEditField)f;
            int cleared = 0;
            IDictionary vals;
            try { vals = f.GetValues(); } catch { continue; }   // element type has no known-flow records
            foreach (DictionaryEntry e in vals)
            {
                double d;
                if (e.Value != null && !(e.Value is DBNull) && double.TryParse(Convert.ToString(e.Value), out d) && !double.IsNaN(d) && d != 0)
                { ef.SetValue((int)e.Key, DBNull.Value); cleared++; }
            }
            if (cleared > 0) log.WriteLine("  cleared {0} known flows on {1}", cleared, et);
        }
    }

    public static void DeleteScenarios(IStormSewerModel m, string labelPrefix, int keepActiveId, TextWriter log)
    {
        var sm = D(m).ScenarioManager;
        sm.ActiveScenarioID = keepActiveId;
        var victims = sm.Elements().Cast<IScenario>().Where(s => s.Label.StartsWith(labelPrefix)).ToList();
        // deepest first: delete a scenario only once it has no children left
        int guard = 0;
        while (victims.Count > 0 && guard++ < 1000)
        {
            var leaf = victims.FirstOrDefault(s => s.Children().Count == 0);
            if (leaf == null) { log.WriteLine("  STOPPED: remaining scenarios still have children"); break; }
            log.WriteLine("  deleted scenario {0} '{1}'", leaf.Id, leaf.Label);
            sm.Delete(leaf.Id);
            victims.Remove(leaf);
        }
    }

    public static void RenameScenario(IStormSewerModel m, int id, string label, TextWriter log)
    {
        var s = (IScenario)D(m).ScenarioManager.Element(id);
        log.WriteLine("  scenario {0}: '{1}' -> '{2}'", id, s.Label, label);
        s.Label = label;
    }

    public static void DeleteTestPump(IStormSewerModel m, TextWriter log)
    {
        var n = m.Network;
        foreach (var p in n.PressurePipes.Elements().ToList()) { log.WriteLine("  deleted pressure pipe " + p.Label); p.Delete(); }
        foreach (var p in n.Pumps.Elements().ToList()) { log.WriteLine("  deleted pump " + p.Label); p.Delete(); }
        foreach (var p in n.PressureJunctions.Elements().ToList()) { log.WriteLine("  deleted pressure junction " + p.Label); p.Delete(); }
        foreach (var p in n.WetWells.Elements().ToList()) { log.WriteLine("  deleted wet well " + p.Label); p.Delete(); }
    }

    public static void CreateOldIdField(IStormSewerModel m, TextWriter log)
    {
        var o = m.UserFieldManager.NewFieldOptions<string>();
        o.Name = "OLD_ID";
        o.Label = "OLD_ID";
        o.Category = "Renaming W17";
        o.ElementType = OpenFlows.StormSewer.Domain.ModelingElements.NetworkElements.StormSewerNetworkElementType.Manhole;
        o.SharedWith.Add(OpenFlows.StormSewer.Domain.ModelingElements.NetworkElements.StormSewerNetworkElementType.Conduit);
        o.SharedWith.Add(OpenFlows.StormSewer.Domain.ModelingElements.NetworkElements.StormSewerNetworkElementType.Outfall);
        m.UserFieldManager.CreateField<string>(o);
        log.WriteLine("  user field OLD_ID created (manholes, conduits, outfalls)");
    }

    // The 10.4 API cannot create text user fields, so the old label goes into the native Notes field.
    public static void OldIdToNotes(IStormSewerModel m, TextWriter log)
    {
        int n = 0, had = 0;
        Action<OpenFlows.Domain.ModelingElements.IElement, string> put = (e, label) =>
        {
            string tag = "OLD_ID=" + label;
            string cur = e.Notes ?? "";
            if (cur.Length > 0 && !cur.StartsWith("OLD_ID=")) { had++; e.Notes = tag + " | " + cur; }
            else e.Notes = tag;
            n++;
        };
        foreach (var e in m.Network.Manholes.Elements()) put(e, e.Label);
        foreach (var e in m.Network.Conduits.Elements()) put(e, e.Label);
        foreach (var e in m.Network.Outfalls.Elements()) put(e, e.Label);
        log.WriteLine("  OLD_ID written to Notes for {0} elements ({1} kept their existing notes after it)", n, had);
    }

    // Copy every current label of the given element type into a text field (OLD_ID).
    public static int FillOldId(IStormSewerModel m, string elementType, string fieldName, TextWriter log)
    {
        var dds = D(m);
        int etId = dds.DomainDataSetType().DomainElementType(elementType).Id;
        var mgr = dds.DomainElementManager(etId);
        var f = (IEditField)mgr.DomainElementField(fieldName);
        var labels = mgr.ModelingElementField("Label").GetValues();
        int n = 0;
        foreach (DictionaryEntry e in labels) { f.SetValue((int)e.Key, Convert.ToString(e.Value)); n++; }
        log.WriteLine("  {0}: OLD_ID filled for {1} elements", elementType, n);
        return n;
    }

    public static void ApplyLabels(IStormSewerModel m, string csvPath, TextWriter log)
    {
        var dds = D(m);
        int n = 0, miss = 0;
        foreach (var line in File.ReadAllLines(csvPath).Skip(1))
        {
            var p = line.Split(',');
            int id = int.Parse(p[0]); string old = p[1], nw = p[2];
            string cur = dds.GetLabelSafe(id);
            if (cur != old) { miss++; if (miss <= 10) log.WriteLine("  MISMATCH id {0}: expected '{1}' found '{2}'", id, old, cur); continue; }
            dds.SetLabelSafe(id, nw); n++;
        }
        log.WriteLine("  {0}: {1} relabelled, {2} mismatches", Path.GetFileName(csvPath), n, miss);
    }
}

public static class DdsExt
{
    static IField LabelField(IDomainDataSet dds, int id)
    {
        int et = dds.DomainElementTypeID(id);
        return dds.DomainElementManager(et).ModelingElementField("Label");
    }
    public static string GetLabelSafe(this IDomainDataSet dds, int id) { return Convert.ToString(LabelField(dds, id).GetValue(id)); }
    public static void SetLabelSafe(this IDomainDataSet dds, int id, string label) { ((IEditField)LabelField(dds, id)).SetValue(id, label); }
}
