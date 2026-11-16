using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Transfer
{
    public const double CFS_PER_LPS = 1.0 / 28.316846592;

    static object ListManager(IStormSewerModel m, string altType, string field, int altId, int mhId, out IEditField colField)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType(altType).Id;
        colField = (IEditField)dds.FieldManager.AlternativeField(field, at, 1, altId);
        return colField.GetValue(mhId);
    }

    // Adds one fixed inflow row (Infiltration and Inflow alternative) to a manhole. flowCfs in storage units.
    public static void AddFixedInflow(IStormSewerModel m, int iiAltId, int mhId, double flowCfs, int inflowType, TextWriter log)
    {
        IEditField col;
        var lm = ListManager(m, "InfiltrationAndInflow", "InflowList", iiAltId, mhId, out col);
        var clm = (ICollectionFieldListManager)lm;
        int row = ((IListManager)lm).Add();
        ((IEditField)clm.Field("InflowType")).SetValue(row, inflowType);
        ((IEditField)clm.Field("FixedLoadType_FixedLoad")).SetValue(row, flowCfs);
        col.SetValue(mhId, lm);
        log.WriteLine("  fixed inflow row {0} on {1}: {2} cfs, type {3}", row, mhId, flowCfs, inflowType);
    }

    // Adds one pattern-load row (base flow, no pattern) to a manhole's sanitary loads.
    public static void AddPatternLoad(IStormSewerModel m, int sanAltId, int mhId, double flowCfs, TextWriter log)
    {
        IEditField col;
        var lm = ListManager(m, "SanitaryLoading", "SanitaryLoads", sanAltId, mhId, out col);
        var clm = (ICollectionFieldListManager)lm;
        int row = ((IListManager)lm).Add();
        ((IEditField)clm.Field("LoadDefinition")).SetValue(row, 2);
        ((IEditField)clm.Field("SanitaryPatternLoadType_SanitaryBaseFlow")).SetValue(row, flowCfs);
        col.SetValue(mhId, lm);
        log.WriteLine("  pattern load row {0} on {1}: {2} cfs", row, mhId, flowCfs);
    }

    // Turns every pattern-load row of the listed manholes into a unit-sanitary-load row carrying the same flow.
    public static int ConvertToUnitLoad(IStormSewerModel m, int sanAltId, IList<int> mhIds, int unitLoadId, int loadDefinition, double unitScale, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var col = (IEditField)dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, sanAltId);
        int n = 0;
        foreach (int id in mhIds)
        {
            var lm = col.GetValue(id);
            var clm = (ICollectionFieldListManager)lm;
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            var rows = dv.Cast<System.Data.DataRowView>().Select(r => new { item = Convert.ToInt32(r["ItemID"]), def = Convert.ToInt32(r["LoadDefinition"]),
                q = r["SanitaryPatternLoadType_SanitaryBaseFlow"] == DBNull.Value ? 0.0 : Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]) }).ToList();
            bool changed = false;
            foreach (var r in rows.Where(r => r.def == 2))
            {
                ((IEditField)clm.Field("LoadDefinition")).SetValue(r.item, loadDefinition);
                ((IEditField)clm.Field("SanitaryUnitLoadType_UnitSanitaryLoadId")).SetValue(r.item, unitLoadId);
                ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(r.item, r.q * unitScale);
                ((IEditField)clm.Field("SanitaryPatternLoadType_SanitaryBaseFlow")).SetValue(r.item, 0.0);
                changed = true; n++;
            }
            if (changed) col.SetValue(id, lm);
        }
        log.WriteLine("  converted {0} rows to unit load {1} (definition {2}, scale {3})", n, unitLoadId, loadDefinition, unitScale);
        return n;
    }

    public static void DumpRows(IStormSewerModel m, string altType, string field, int altId, int mhId, TextWriter log)
    {
        IEditField col;
        var lm = ListManager(m, altType, field, altId, mhId, out col);
        Probe.DumpTable(lm, log);
    }

    // Typed result flow (display units, m3/d) summed over the conduits touching each outfall.
    public static Dictionary<string, double> OutfallFlows(IStormSewerModel m)
    {
        var res = new Dictionary<string, double>();
        var of = m.Network.Outfalls.Elements().ToDictionary(o => o.Id, o => o.Label);
        foreach (var c in m.Network.Conduits.Elements())
        {
            int a = c.Input.StartNode.Id, b = c.Input.StopNode.Id;
            string lab = of.ContainsKey(a) ? of[a] : of.ContainsKey(b) ? of[b] : null;
            if (lab == null) continue;
            var q = c.Results.Flow();
            if (!q.HasValue) continue;
            res[lab] = (res.ContainsKey(lab) ? res[lab] : 0) + q.Value;
        }
        return res;
    }
}
