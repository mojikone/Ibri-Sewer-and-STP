using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class LoadsDiag
{
    public const double M3D_PER_CFS = 2446.575545;
    public const double LPS_PER_CFS = 28.316846592;

    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    // Per sanitary alternative: rows per manhole, totals, duplicate rows; per-row export for later checks.
    public static void Run(IStormSewerModel m, string outDir, string probeLabel, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int at = dds.DomainDataSetType().AlternativeType("SanitaryLoading").Id;
        var am = dds.AlternativeManager(at);
        var labels = dds.DomainElementManager(1).ModelingElementField("Label").GetValues();
        int probeId = -1;
        foreach (DictionaryEntry e in labels) if (Convert.ToString(e.Value) == probeLabel) probeId = (int)e.Key;
        foreach (IAlternative alt in am.Elements())
        {
            var col = dds.FieldManager.AlternativeField("SanitaryLoads", at, 1, alt.Id);
            var cnt = dds.FieldManager.AlternativeField("SanitaryLoadsCount", at, 1, alt.Id).GetValues();
            var hist = new SortedDictionary<int, int>();
            double total = 0; int dupMh = 0, zeroRows = 0, rowsAll = 0;
            using (var w = new StreamWriter(Path.Combine(outDir, "rows_" + alt.Label + ".csv"), false, new UTF8Encoding(false)))
            {
                w.WriteLine("mh_id,label,item,def,base_m3d");
                foreach (DictionaryEntry e in cnt)
                {
                    int c = Convert.ToInt32(e.Value ?? 0);
                    hist[c] = hist.ContainsKey(c) ? hist[c] + 1 : 1;
                    if (c == 0) continue;
                    int id = (int)e.Key;
                    var dv = View(col.GetValue(id));
                    var qs = new List<double>();
                    foreach (System.Data.DataRowView r in dv)
                    {
                        double q = r["SanitaryPatternLoadType_SanitaryBaseFlow"] == DBNull.Value ? 0 : Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]);
                        qs.Add(q); total += q; rowsAll++; if (q == 0) zeroRows++;
                        w.WriteLine("{0},{1},{2},{3},{4}", id, labels[id], r["ItemID"], r["LoadDefinition"], (q * M3D_PER_CFS).ToString("R"));
                    }
                    if (qs.Count != qs.Distinct().Count()) dupMh++;
                }
            }
            log.WriteLine("sanitary '{0}' ({1}): rows {2}, total {3:n1} m3/d, zero rows {4}, manholes with an identical repeated row {5}",
                alt.Label, alt.Id, rowsAll, total * M3D_PER_CFS, zeroRows, dupMh);
            log.WriteLine("   rows per manhole: " + string.Join(", ", hist.Select(kv => kv.Key + ":" + kv.Value)));
            if (probeId > 0)
            {
                var dv = View(col.GetValue(probeId));
                log.WriteLine("   {0} rows: {1}", probeLabel, string.Join(" ; ", dv.Cast<System.Data.DataRowView>().Select(r =>
                    "def " + r["LoadDefinition"] + " " + (r["SanitaryPatternLoadType_SanitaryBaseFlow"] == DBNull.Value ? 0 : Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]) * M3D_PER_CFS).ToString("n3") + " m3/d")));
            }
        }

        log.WriteLine("== extreme flow factor tables (base load L/s -> factor)");
        var st = dds.DomainDataSetType().SupportElementType("ExtremeFlowFactor");
        var sm = dds.SupportElementManager(st.Id);
        var curve = dds.FieldManager.SupportElementField("EffTableCurve", st.Id);
        foreach (IModelingElement el in sm.Elements())
        {
            var dv = View(curve.GetValue(el.Id));
            log.WriteLine("  " + el.Label + ": " + string.Join("  ", dv.Cast<System.Data.DataRowView>().Select(r =>
                (Convert.ToDouble(r["EffTableCurve_BaseLoad"]) * LPS_PER_CFS).ToString("0.###") + "->" + Convert.ToDouble(r["EffTableCurve_ExtremeFlowFactor"]).ToString("0.###"))));
        }

        log.WriteLine("== unit sanitary load definitions");
        var ust = dds.DomainDataSetType().SupportElementType("UnitSanitaryLoad");
        foreach (IModelingElement el in dds.SupportElementManager(ust.Id).Elements())
            foreach (IField f in dds.FieldManager.SupportElementFields(ust.Id))
                log.WriteLine("  {0} | {1} = {2}", el.Label, f.Name, f.GetValue(el.Id));
        foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
        {
            Type[] ts; try { ts = asm.GetTypes(); } catch { continue; }
            foreach (var t in ts.Where(t => t.IsEnum && (t.Name == "UnitSanitaryLoadType" || t.Name.Contains("UnitSanitaryLoadType") || t.Name.Contains("SanitaryLoadDefinition") || t.Name == "LoadDefinition")))
                log.WriteLine("  enum {0}: {1}", t.FullName, string.Join(", ", Enum.GetNames(t).Select(n => n + "=" + Convert.ToInt32(Enum.Parse(t, n)))));
        }
    }
}
