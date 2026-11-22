using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// W19 G7: the loads of a scenario, written as SewerGEMS returns them through the documented API (every column of every
// sanitary-load row), and the support elements that define unit loads, so the app can rebuild the loads.
public static class LoadsDump
{
    static string Q(object o)
    {
        var s = o == null || o == DBNull.Value ? "" : Convert.ToString(o, System.Globalization.CultureInfo.InvariantCulture);
        return s.Contains(",") || s.Contains("\"") || s.Contains("\n") ? "\"" + s.Replace("\"", "\"\"") + "\"" : s;
    }

    public static int AltOf(IStormSewerModel m, int scenarioId, string altType)
    {
        var dds = m.DomainDataSet;
        var s = (IScenario)dds.ScenarioManager.Element(scenarioId);
        return s.AlternativeID(dds.DomainDataSetType().AlternativeType(altType).Id);
    }

    // every column of every sanitary row, per element, of the scenario's sanitary-loading alternative
    public static void SanitaryRows(IStormSewerModel m, int scenarioId, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int sanT = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        int alt = AltOf(m, scenarioId, "SanitaryLoading");
        log.WriteLine("  scenario {0}: sanitary alternative {1}", scenarioId, alt);
        var f = dds.FieldManager.AlternativeField("SanitaryLoads", sanT, 1, alt);
        var cnt = dds.FieldManager.AlternativeField("SanitaryLoadsCount", sanT, 1, alt).GetValues();
        List<string> cols = null; int n = 0;
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            foreach (DictionaryEntry e in cnt)
            {
                if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
                int id = (int)e.Key;
                var lm = f.GetValue(id);
                var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
                if (cols == null)
                {
                    cols = dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName).ToList();
                    w.WriteLine("element_id," + string.Join(",", cols));
                }
                foreach (System.Data.DataRowView r in dv) { w.WriteLine(id + "," + string.Join(",", cols.Select(c => Q(r[c])))); n++; }
            }
        }
        log.WriteLine("  {0} sanitary rows written; columns: {1}", n, cols == null ? "-" : string.Join(" | ", cols));
    }

    // the loads of one scenario per element, in m3/d: unit loads (units x the unit load) and pattern loads (base flow),
    // from SewerGEMS's stored values (cfs), with the unit load's id so the peaking table can be matched
    public const double M3D_PER_CFS = 2446.575545;
    public static void ScenarioLoads(IStormSewerModel m, int scenarioId, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int sanT = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        int alt = AltOf(m, scenarioId, "SanitaryLoading");
        var unit = new Dictionary<int, double>();
        var ust = dds.DomainDataSetType().SupportElementType("UnitSanitaryLoad");
        var uf = dds.FieldManager.SupportElementField("UnitSanitaryLoad_UnitLoad", ust.Id);
        foreach (IModelingElement el in dds.SupportElementManager(ust.Id).Elements())
            unit[el.Id] = Convert.ToDouble(uf.GetValue(el.Id));
        var f = dds.FieldManager.AlternativeField("SanitaryLoads", sanT, 1, alt);
        var cnt = dds.FieldManager.AlternativeField("SanitaryLoadsCount", sanT, 1, alt).GetValues();
        var ci = System.Globalization.CultureInfo.InvariantCulture; int n = 0;
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            w.WriteLine("element_id,unit_m3d,pattern_m3d,unit_load_ids");
            foreach (DictionaryEntry e in cnt)
            {
                if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
                int id = (int)e.Key;
                var lm = f.GetValue(id);
                var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
                double u = 0, pq = 0; var ids = new HashSet<int>();
                foreach (System.Data.DataRowView r in dv)
                {
                    int def = Convert.ToInt32(r["LoadDefinition"]);
                    if (def == 1 && r["SanitaryUnitLoadType_UnitSanitaryLoadId"] != DBNull.Value)
                    {
                        int uid = Convert.ToInt32(r["SanitaryUnitLoadType_UnitSanitaryLoadId"]); ids.Add(uid);
                        u += Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]) * (unit.ContainsKey(uid) ? unit[uid] : 0.0);
                    }
                    else if (r["SanitaryPatternLoadType_SanitaryBaseFlow"] != DBNull.Value)
                        pq += Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]);
                }
                w.WriteLine(string.Join(",", id, (u * M3D_PER_CFS).ToString("R", ci), (pq * M3D_PER_CFS).ToString("R", ci), string.Join("/", ids)));
                n++;
            }
        }
        log.WriteLine("  scenario {0}: loads on {1} elements (sanitary alternative {2})", scenarioId, n, alt);
    }

    // support element types whose name speaks of loads or flows, with every field of every element
    public static void SupportLoads(IStormSewerModel m, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet;
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            w.WriteLine("type,element_id,label,field,value");
            foreach (ISupportElementType st in dds.DomainDataSetType().SupportElementTypes())
            {
                string nm = st.Name ?? "";
                string lo = nm.ToLowerInvariant();
                if (!(lo.Contains("load") || lo.Contains("extreme") || lo.Contains("peak") || lo.Contains("infiltration") || lo.Contains("sanitary"))) continue;
                log.WriteLine("  support type {0} '{1}'", st.Id, nm);
                ISupportElementManager mgr;
                try { mgr = dds.SupportElementManager(st.Id); } catch { continue; }
                FieldCollection fc;
                try { fc = dds.FieldManager.SupportElementFields(st.Id); } catch { continue; }
                foreach (IModelingElement el in mgr.Elements())
                    foreach (IField fd in fc)
                    {
                        object v;
                        try { v = fd.GetValue(el.Id); } catch (Exception ex) { v = "ERR:" + ex.GetType().Name; }
                        var vs = v as IEnumerable;
                        string val;
                        if (v != null && !(v is string) && vs != null) { val = "(collection)"; }
                        else
                        {
                            try
                            {
                                var dvp = v == null ? null : v.GetType().GetProperty("DataView");
                                if (dvp != null)
                                {
                                    var dv = (System.Data.DataView)dvp.GetValue(v, null);
                                    var cols = dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName).ToList();
                                    val = string.Join(" ; ", dv.Cast<System.Data.DataRowView>().Select(r => string.Join("|", cols.Select(c => c + "=" + Convert.ToString(r[c], System.Globalization.CultureInfo.InvariantCulture)))));
                                }
                                else val = Convert.ToString(v, System.Globalization.CultureInfo.InvariantCulture);
                            }
                            catch { val = Convert.ToString(v); }
                        }
                        w.WriteLine(string.Join(",", Q(nm), el.Id, Q(el.Label), Q(fd.Name), Q(val)));
                    }
            }
        }
    }
}
