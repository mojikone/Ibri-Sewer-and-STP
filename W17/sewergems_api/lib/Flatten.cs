using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Flatten
{
    // Effective (inherited-resolved) values of every scalar physical field, for manholes, conduits and outfalls.
    public static Dictionary<string, string> Snapshot(IStormSewerModel m, int physAltId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int pt = dds.DomainDataSetType().AlternativeType("Physical").Id;
        var snap = new Dictionary<string, string>();
        foreach (int et in new[] { 1, 3, 5 })
        {
            int nf = 0;
            foreach (IField f in dds.FieldManager.AlternativeFields(pt, et, physAltId))
            {
                if (f.FieldDataType == FieldDataType.Collection || f.FieldDataType == FieldDataType.LongBinary) continue;
                IDictionary vals;
                try { vals = f.GetValues(); } catch { continue; }
                nf++;
                foreach (DictionaryEntry e in vals) snap[et + "|" + f.Name + "|" + e.Key] = Convert.ToString(e.Value, System.Globalization.CultureInfo.InvariantCulture);
            }
            log.WriteLine("  snapshot type {0}: {1} fields", et, nf);
        }
        log.WriteLine("  snapshot of alt {0}: {1} values", physAltId, snap.Count);
        return snap;
    }

    public static int Compare(Dictionary<string, string> a, Dictionary<string, string> b, TextWriter log)
    {
        int diff = 0;
        foreach (var kv in a)
        {
            string v; if (!b.TryGetValue(kv.Key, out v)) v = "<missing>";
            if (v != kv.Value) { if (++diff <= 15) log.WriteLine("    DIFF {0}: {1} -> {2}", kv.Key, kv.Value, v); }
        }
        log.WriteLine("  compared {0} values: {1} differ", a.Count, diff);
        var groups = a.Where(kv => { string v; return !b.TryGetValue(kv.Key, out v) || v != kv.Value; })
            .GroupBy(kv => { var p = kv.Key.Split('|'); string v; b.TryGetValue(kv.Key, out v); return p[0] + "|" + p[1] + "  " + kv.Value + " -> " + (v ?? "<missing>"); })
            .OrderByDescending(g => g.Count());
        foreach (var g in groups.Take(40)) log.WriteLine("    {0,6} x {1}", g.Count(), g.Key);
        return diff;
    }

    public static void AddChildren(IStormSewerModel m, int parentId, string[] labels, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var am = dds.AlternativeManager(dds.DomainDataSetType().AlternativeType("Physical").Id);
        foreach (var lab in labels)
        {
            int id = am.Add(parentId);
            ((IAlternative)am.Element(id)).Label = lab;
            log.WriteLine("  physical child {0} '{1}' under {2}", id, lab, parentId);
        }
    }

    // Merge the alternative into its parent, repeatedly, until the values sit in the base alternative.
    public static void MergeChain(IStormSewerModel m, int leafId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int pt = dds.DomainDataSetType().AlternativeType("Physical").Id;
        var am = dds.AlternativeManager(pt);
        // alternatives that are not on the leaf-to-base chain and that no scenario uses: delete, deepest first
        var chain = new HashSet<int>();
        for (int c = leafId; c != 0; c = ((IAlternative)am.Element(c)).ParentID) chain.Add(c);
        bool again = true;
        while (again)
        {
            again = false;
            foreach (IAlternative a in am.Elements().Cast<IAlternative>().ToList())
            {
                if (chain.Contains(a.Id) || a.ParentID == 0 || a.Children().Count > 0 || a.ReferencedScenarios().Count > 0) continue;
                log.WriteLine("  deleted off-chain alternative {0} '{1}'", a.Id, a.Label);
                am.Delete(a.Id); again = true;
            }
        }
        int cur = leafId;
        int guard = 0;
        while (guard++ < 100)
        {
            var a = (IAlternative)am.Element(cur);
            int parent = a.ParentID;
            if (parent == 0) { log.WriteLine("  reached base alternative {0} '{1}'", cur, a.Label); break; }
            foreach (IScenario s in dds.ScenarioManager.Elements())
                if (s.AlternativeID(pt) == cur) s.AlternativeID(pt, parent);
            am.Merge(cur);
            bool stillThere = am.Exists(cur);
            log.WriteLine("  merged {0} into {1}; child still exists: {2}", cur, parent, stillThere);
            cur = parent;
        }
    }
}
