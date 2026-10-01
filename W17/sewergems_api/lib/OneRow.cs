using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class OneRow
{
    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    // Every manhole that carries several unit-load rows of the same unit load gets one row with their sum.
    public static void MergeUnitRows(IStormSewerModel m, int altId, int unitLoadId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var col = (IEditField)dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, altId);
        var cntF = dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId);
        double before = 0, after = 0; int merged = 0, removed = 0, skipped = 0;
        foreach (DictionaryEntry e in cntF.GetValues())
        {
            if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
            int id = (int)e.Key;
            var lm = col.GetValue(id);
            var rows = View(lm).Cast<System.Data.DataRowView>().Select((r, pos) => new { pos = pos,
                item = Convert.ToInt32(r["ItemID"]), def = Convert.ToInt32(r["LoadDefinition"]),
                ul = r["SanitaryUnitLoadType_UnitSanitaryLoadId"] == DBNull.Value ? -1 : Convert.ToInt32(r["SanitaryUnitLoadType_UnitSanitaryLoadId"]),
                n = r["SanitaryUnitLoadType_LoadingUnitNumber"] == DBNull.Value ? 0.0 : Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]) }).ToList();
            foreach (var r in rows) if (r.def == 1) before += r.n;
            var unit = rows.Where(r => r.def == 1 && r.ul == unitLoadId).ToList();
            if (rows.Count != unit.Count) skipped++;          // anything that is not a plot unit load is left alone
            if (unit.Count > 1)
            {
                var clm = (ICollectionFieldListManager)lm;
                ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(unit[0].item, unit.Sum(r => r.n));
                foreach (var r in unit.Skip(1).OrderByDescending(x => x.pos)) { ((IListManager)lm).Delete(r.pos); removed++; }
                col.SetValue(id, lm); merged++;
            }
        }
        var hist = new SortedDictionary<int, int>();
        foreach (DictionaryEntry e in cntF.GetValues())
        {
            int c = Convert.ToInt32(e.Value ?? 0); hist[c] = hist.ContainsKey(c) ? hist[c] + 1 : 1;
            if (c == 0) continue;
            foreach (System.Data.DataRowView r in View(col.GetValue((int)e.Key)))
                if (Convert.ToInt32(r["LoadDefinition"]) == 1) after += Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]);
        }
        var alt = (IAlternative)dds.AlternativeManager(at).Element(altId);
        log.WriteLine("  '{0}': {1} manholes merged, {2} rows removed, {3} manholes with other loads left alone; total {4:n2} -> {5:n2} m3/d; rows per manhole now {6}",
            alt.Label, merged, removed, skipped, before, after, string.Join(", ", hist.Select(kv => kv.Key + ":" + kv.Value)));
    }

    // Remove every row of one load definition (1 = unit load) from an alternative; reports what was removed and where.
    public static void DeleteRowsOfDefinition(IStormSewerModel m, int altId, int definition, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var col = (IEditField)dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, altId);
        var labels = dds.DomainElementManager(1).ModelingElementField("Label").GetValues();
        int n = 0, mh = 0; double units = 0;
        using (var w = new StreamWriter(csv, true))
        {
            foreach (DictionaryEntry e in dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId).GetValues())
            {
                if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
                int id = (int)e.Key;
                var lm = col.GetValue(id);
                var hits = View(lm).Cast<System.Data.DataRowView>().Select((r, pos) => new { pos = pos, def = Convert.ToInt32(r["LoadDefinition"]),
                    others = 0, n = r["SanitaryUnitLoadType_LoadingUnitNumber"] == DBNull.Value ? 0.0 : Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]) }).ToList();
                var del = hits.Where(h => h.def == definition).ToList();
                if (del.Count == 0) continue;
                foreach (var h in del.OrderByDescending(x => x.pos)) { ((IListManager)lm).Delete(h.pos); n++; units += h.n; }
                col.SetValue(id, lm); mh++;
                w.WriteLine("{0},{1},{2},{3},{4}", altId, labels[id], del.Count, del.Sum(h => h.n), hits.Count - del.Count);
            }
        }
        log.WriteLine("  alt {0}: removed {1} rows of definition {2} on {3} manholes ({4:n2} loading units)", altId, n, definition, mh, units);
    }

    // Insert a row (base load in L/s, factor) into a tabular extreme-flow method, after the last row with a smaller base load.
    public static void AddTableRow(IStormSewerModel m, string methodLabel, double baseLps, double factor, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("ExtremeFlowFactor");
        var sm = dds.SupportElementManager(st.Id);
        var el = sm.Elements().Cast<IModelingElement>().First(x => x.Label == methodLabel);
        var curve = (IEditField)dds.FieldManager.SupportElementField("EffTableCurve", st.Id);
        var lm = curve.GetValue(el.Id);
        var dv = View(lm);
        double cfs = baseLps / 28.316846592;
        int pos = dv.Cast<System.Data.DataRowView>().Count(r => Convert.ToDouble(r["EffTableCurve_BaseLoad"]) < cfs);
        int item = ((IOrderedListManager)lm).Insert(pos);
        var clm = (ICollectionFieldListManager)lm;
        ((IEditField)clm.Field("EffTableCurve_BaseLoad")).SetValue(item, cfs);
        ((IEditField)clm.Field("EffTableCurve_ContributingPopulation")).SetValue(item, 0.0);
        ((IEditField)clm.Field("EffTableCurve_ExtremeFlowFactor")).SetValue(item, factor);
        curve.SetValue(el.Id, lm);
        log.WriteLine("  '{0}': row inserted at position {1}: {2} L/s -> {3}", methodLabel, pos, baseLps, factor);
        log.WriteLine("    table now: " + string.Join("  ", View(curve.GetValue(el.Id)).Cast<System.Data.DataRowView>().Select(r =>
            (Convert.ToDouble(r["EffTableCurve_BaseLoad"]) * 28.316846592).ToString("0.###") + "->" + Convert.ToDouble(r["EffTableCurve_ExtremeFlowFactor"]).ToString("0.###"))));
    }
}
