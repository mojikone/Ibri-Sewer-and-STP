using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// W18: one year's plot loads written into a sanitary alternative (a child of the 2070 loads), one unit-load row per
// manhole, count = m3/d (the unit load is discharge-based, 1 m3/d per unit, since R2).
public static class YearLoads
{
    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    public static Dictionary<int, double> ReadColumn(string csv, string column)
    {
        var lines = File.ReadAllLines(csv);
        var head = lines[0].Split(',');
        int c = Array.IndexOf(head, column);
        if (c < 0) throw new Exception("column " + column + " not in " + csv);
        var d = new Dictionary<int, double>();
        foreach (var l in lines.Skip(1))
        {
            var p = l.Split(',');
            d[int.Parse(p[0])] = double.Parse(p[c], System.Globalization.CultureInfo.InvariantCulture);
        }
        return d;
    }

    // Sets every manhole's plot unit-load row to the year's flow; inserts a row where a manhole has none and needs one.
    // Throws if the stored total differs from the file's total by more than 0.01 m3/d.
    public static void SetYear(IStormSewerModel m, int altId, int unitLoadId, string csv, string column, TextWriter log)
    {
        var q = ReadColumn(csv, column);
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var col = (IEditField)dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, altId);
        var cntF = dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId);
        var withRows = new HashSet<int>();
        int set = 0, zeroed = 0, inserted = 0, odd = 0;
        foreach (DictionaryEntry e in cntF.GetValues())
        {
            if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
            int id = (int)e.Key;
            var lm = col.GetValue(id);
            var clm = (ICollectionFieldListManager)lm;
            var unit = View(lm).Cast<System.Data.DataRowView>().Where(r => Convert.ToInt32(r["LoadDefinition"]) == 1 &&
                r["SanitaryUnitLoadType_UnitSanitaryLoadId"] != DBNull.Value &&
                Convert.ToInt32(r["SanitaryUnitLoadType_UnitSanitaryLoadId"]) == unitLoadId).Select(r => Convert.ToInt32(r["ItemID"])).ToList();
            if (unit.Count == 0) continue;
            withRows.Add(id);
            if (unit.Count > 1) odd++;
            double v = q.ContainsKey(id) ? q[id] : 0.0;
            ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(unit[0], v);
            foreach (var item in unit.Skip(1)) ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(item, 0.0);
            col.SetValue(id, lm);
            if (v > 0) set++; else zeroed++;
        }
        foreach (var kv in q)
        {
            if (kv.Value <= 0 || withRows.Contains(kv.Key)) continue;
            var lm = col.GetValue(kv.Key);
            var clm = (ICollectionFieldListManager)lm;
            int row = ((IListManager)lm).Add();
            ((IEditField)clm.Field("LoadDefinition")).SetValue(row, 1);
            ((IEditField)clm.Field("SanitaryUnitLoadType_UnitSanitaryLoadId")).SetValue(row, unitLoadId);
            ((IEditField)clm.Field("SanitaryUnitLoadType_LoadingUnitNumber")).SetValue(row, kv.Value);
            col.SetValue(kv.Key, lm);
            inserted++;
        }
        double stored = 0;
        foreach (DictionaryEntry e in dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, altId).GetValues())
        {
            if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
            foreach (System.Data.DataRowView r in View(col.GetValue((int)e.Key)))
                if (Convert.ToInt32(r["LoadDefinition"]) == 1) stored += Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]);
        }
        double want = q.Values.Sum();
        log.WriteLine("  {0}: {1} manholes set, {2} set to zero, {3} rows inserted, {4} manholes with several rows; file {5:n2}, stored {6:n2} m3/d",
            column, set, zeroed, inserted, odd, want, stored);
        if (Math.Abs(stored - want) > 0.01) throw new Exception(string.Format("{0}: stored {1:n2} against {2:n2} m3/d", column, stored, want));
    }
}
