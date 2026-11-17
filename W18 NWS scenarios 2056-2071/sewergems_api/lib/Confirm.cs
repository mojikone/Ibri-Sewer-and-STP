using System;
using System.IO;
using System.Linq;
using System.Text.RegularExpressions;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// Read-only confirmation of a W18 model (engineer, 2026-11-17): per scenario, which alternatives and calculation options
// it uses; whether its sanitary loads are unit loads (peaked by the extreme flow setup) or pattern loads (not peaked);
// the unit load definitions; the calculation options' extreme-flow and infiltration settings; the extreme flow setups;
// and every field of the infiltration-and-inflow alternative on conduits and manholes, summarised. Nothing is saved.
public static class Confirm
{
    public const double M3D_PER_CFS = 2446.575545;
    static System.Data.DataView View(object lm) { return (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null); }

    static string Summ(IField f)
    {
        IDictionary vals; try { vals = f.GetValues(); } catch (Exception ex) { return "<" + ex.GetType().Name + ">"; }
        var g = new Dictionary<string, int>(); double sum = 0; int num = 0;
        foreach (DictionaryEntry e in vals)
        {
            string k = Convert.ToString(e.Value);
            if (e.Value != null && e.Value.GetType().GetProperty("DataView") != null) k = "<table>";
            g[k] = g.ContainsKey(k) ? g[k] + 1 : 1;
            double d; if (e.Value is IConvertible && double.TryParse(k, out d) && !double.IsNaN(d)) { sum += d; num++; }
        }
        return string.Format("{0} values, {1} distinct; top: {2}{3}", vals.Count, g.Count,
            string.Join("; ", g.OrderByDescending(kv => kv.Value).Take(4).Select(kv => kv.Key + " x" + kv.Value)),
            num > 0 ? string.Format("; sum {0:G6}", sum) : "");
    }

    public static void Run(IStormSewerModel m, string[] scenarioLabels, TextWriter log)
    {
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType(); var fm = dds.FieldManager; var sm = dds.ScenarioManager;
        int sat = dst.AlternativeType("SanitaryLoading").Id;
        var calcIds = new HashSet<int>(); var iiIds = new HashSet<int>(); var physIds = new HashSet<int>();
        foreach (var lab in scenarioLabels)
        {
            var s = sm.Elements().Cast<IScenario>().FirstOrDefault(x => x.Label == lab);
            if (s == null) { log.WriteLine("== no scenario '" + lab + "'"); continue; }
            log.WriteLine("== scenario '{0}' ({1}), parent {2}", lab, s.Id, s.ParentID);
            foreach (var tn in new[] { "Physical", "SanitaryLoading", "InfiltrationAndInflow", "Design", "SystemFlows" })
            {
                try { log.WriteLine("  {0} = {1}{2}", tn, s.AlternativeID(tn), s.IsAlternativeLocal(dst.AlternativeType(tn).Id) ? " (local)" : " (inherited)"); }
                catch (Exception ex) { log.WriteLine("  {0}: {1}", tn, ex.Message); }
            }
            int co = s.CalculationOptionsID("DelawareProductEngine"); calcIds.Add(co);
            log.WriteLine("  calculation options {0}", co);
            try { iiIds.Add(s.AlternativeID("InfiltrationAndInflow")); physIds.Add(s.AlternativeID("Physical")); } catch { }
            int sa = s.AlternativeID("SanitaryLoading");
            var col = fm.AlternativeField("SanitaryLoads", sat, 1, sa);
            int mh = 0, pos = 0, unitRows = 0, otherRows = 0; double units = 0, pattern = 0; var uid = new SortedDictionary<int, int>();
            foreach (DictionaryEntry e in fm.AlternativeField("SanitaryLoadsCount", sat, 1, sa).GetValues())
            {
                if (Convert.ToInt32(e.Value ?? 0) == 0) continue;
                mh++; bool p = false;
                foreach (System.Data.DataRowView r in View(col.GetValue((int)e.Key)))
                {
                    if (Convert.ToInt32(r["LoadDefinition"]) == 1)
                    {
                        unitRows++;
                        int u = r["SanitaryUnitLoadType_UnitSanitaryLoadId"] == DBNull.Value ? -1 : Convert.ToInt32(r["SanitaryUnitLoadType_UnitSanitaryLoadId"]);
                        uid[u] = uid.ContainsKey(u) ? uid[u] + 1 : 1;
                        double v = Convert.ToDouble(r["SanitaryUnitLoadType_LoadingUnitNumber"]); units += v; if (v > 0) p = true;
                    }
                    else
                    {
                        otherRows++;
                        pattern += r["SanitaryPatternLoadType_SanitaryBaseFlow"] == DBNull.Value ? 0 : Convert.ToDouble(r["SanitaryPatternLoadType_SanitaryBaseFlow"]) * M3D_PER_CFS;
                    }
                }
                if (p) pos++;
            }
            log.WriteLine("  sanitary alternative {0}: {1} manholes with rows, {2} with a load > 0; unit-load rows {3} (unit loads {4}) total {5:n2} units; pattern-load rows {6} total {7:n2} m3/d",
                sa, mh, pos, unitRows, string.Join(", ", uid.Select(kv => kv.Key + " x" + kv.Value)), units, otherRows, pattern);
        }

        log.WriteLine("== unit sanitary load definitions");
        var ust = dst.SupportElementType("UnitSanitaryLoad");
        foreach (IModelingElement el in dds.SupportElementManager(ust.Id).Elements())
            foreach (IField f in fm.SupportElementFields(ust.Id))
            {
                object v; try { v = f.GetValue(el.Id); } catch (Exception ex) { v = "<" + ex.GetType().Name + ">"; }
                log.WriteLine("  {0} '{1}' | {2} = {3}", el.Id, el.Label, f.Name, v);
            }

        log.WriteLine("== calculation options (extreme flow, infiltration, sanitary)");
        var com = sm.CalculationOptionsManager("DelawareProductEngine");
        foreach (int co in calcIds)
            foreach (IField f in com.SupportedFields())
                if (Regex.IsMatch(f.Name, "Extreme|Peak|Infiltr|Sanitary|Unit|Wet|Dry", RegexOptions.IgnoreCase))
                {
                    object v; try { v = f.GetValue(co); } catch (Exception ex) { v = "<" + ex.GetType().Name + ">"; }
                    log.WriteLine("  {0} | {1} = {2}", co, f.Name, v);
                }

        foreach (string sname in new[] { "ExtremeFlowSetup", "ExtremeFlowFactor" })
        {
            var st = dst.SupportElementType(sname);
            log.WriteLine("== support " + sname);
            foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
            {
                log.WriteLine("  element " + el.Id + " '" + el.Label + "'");
                foreach (IField f in fm.SupportElementFields(st.Id))
                {
                    object v; try { v = f.GetValue(el.Id); } catch (Exception ex) { v = "<" + ex.GetType().Name + ">"; }
                    if (v != null && v.GetType().GetProperty("DataView") != null)
                    {
                        var dv = View(v);
                        log.WriteLine("    {0}: {1} rows | {2}", f.Name, dv.Count, string.Join(" ; ", dv.Cast<System.Data.DataRowView>().Take(12).Select(r =>
                            string.Join(", ", dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName + "=" + r[c.ColumnName])))));
                    }
                    else log.WriteLine("    {0} = {1}", f.Name, v);
                }
            }
        }

        int iit = dst.AlternativeType("InfiltrationAndInflow").Id;
        foreach (int ii in iiIds)
            foreach (int et in new[] { 3, 1 })
            {
                log.WriteLine("== infiltration and inflow alternative {0}, element type {1} ({2})", ii, et, et == 3 ? "conduits" : "manholes");
                FieldCollection fc; try { fc = fm.AlternativeFields(iit, et, ii); } catch (Exception ex) { log.WriteLine("  " + ex.Message); continue; }
                foreach (IField f in fc) log.WriteLine("  {0}: {1}", f.Name, Summ(f));
            }
        int pt = dst.AlternativeType("Physical").Id;
        foreach (int ph in physIds)
        {
            log.WriteLine("== physical alternative {0}, conduit length fields", ph);
            foreach (IField f in fm.AlternativeFields(pt, 3, ph)) if (Regex.IsMatch(f.Name, "Length", RegexOptions.IgnoreCase)) log.WriteLine("  {0}: {1}", f.Name, Summ(f));
        }
    }
}
