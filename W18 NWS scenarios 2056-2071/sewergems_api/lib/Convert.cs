using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class Convert2
{
    public const double M3D_PER_CFS = 2446.575545;

    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    // The unit load becomes discharge-based, 1 m3/d per unit, so a loading-unit count reads as m3/d.
    public static void SetUnitLoad(IStormSewerModel m, int unitLoadId, string label, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int st = dds.DomainDataSetType().SupportElementType("UnitSanitaryLoad").Id;
        var fm = dds.FieldManager;
        ((IEditField)fm.SupportElementField("UnitSanitaryLoadType", st)).SetValue(unitLoadId, 2);          // DischargeBased
        ((IEditField)fm.SupportElementField("UnitSanitaryLoad_UnitLoad", st)).SetValue(unitLoadId, 1.0 / M3D_PER_CFS);
        var el = dds.SupportElementManager(st).Element(unitLoadId);
        log.WriteLine("  unit load {0} '{1}' -> '{2}', discharge-based, 1 m3/d per unit", unitLoadId, el.Label, label);
        el.Label = label;
    }

    // Every pattern-load row becomes a unit-load row with the same flow (count = flow in m3/d). Returns totals before/after.
    public static void ConvertAlternative(IStormSewerModel m, int altId, int unitLoadId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var col = (IEditField)dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, altId);
        var cnt = dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId).GetValues();
        double before = 0, after = 0; int rows = 0, other = 0, mhs = 0;
        foreach (DictionaryEntry e in cnt)
        {
            if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
            int id = (int)e.Key;
            var lm = col.GetValue(id);
            var clm = (ICollectionFieldListManager)lm;
            var items = View(lm).Cast<System.Data.DataRowView>().Select(r => new {
                item = Convert.ToInt32(r["ItemID"]), def = Convert.ToInt32(r["LoadDefinition"]),
                q = r["SanitaryPatternLoadType_SanitaryBaseFlow"] == DBNull.Value ? 0.0 : Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]) }).ToList();
            bool changed = false;
            foreach (var r in items)
            {
                if (r.def != 2) { other++; continue; }
                before += r.q;
                double units = r.q * M3D_PER_CFS;
                ((IEditField)clm.Field("LoadDefinition")).SetValue(r.item, 1);
                ((IEditField)clm.Field("SanitaryUnitLoadType_UnitSanitaryLoadId")).SetValue(r.item, unitLoadId);
                ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(r.item, units);
                ((IEditField)clm.Field("SanitaryPatternLoadType_SanitaryBaseFlow")).SetValue(r.item, 0.0);
                after += units / M3D_PER_CFS;
                rows++; changed = true;
            }
            if (changed) { col.SetValue(id, lm); mhs++; }
        }
        // read back what was stored
        double check = 0; int checkRows = 0, left = 0;
        foreach (DictionaryEntry e in dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId).GetValues())
        {
            if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
            foreach (System.Data.DataRowView r in View(col.GetValue((int)e.Key)))
            {
                int def = Convert.ToInt32(r["LoadDefinition"]);
                if (def == 1) { check += Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]); checkRows++; }
                else if (def == 2) left++;
            }
        }
        var alt = (IAlternative)dds.AlternativeManager(at).Element(altId);
        log.WriteLine("  '{0}': {1} rows on {2} manholes converted; before {3:n2} m3/d, stored after {4:n2} m3/d ({5} unit rows read back); pattern rows left {6}; other rows untouched {7}",
            alt.Label, rows, mhs, before * M3D_PER_CFS, check, checkRows, left, other);
    }
}
