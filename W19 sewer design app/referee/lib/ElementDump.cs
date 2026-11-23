using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// W19 (2026-11-23): every element of a model, of every type, with every input field of the scenario's alternatives,
// its geometry and the result fields at the first time step: to learn what a model holds (ponds, catchments, pumps,
// wet wells...) through SewerGEMS's documented API only. Read only; the job works on a copy.
public static class ElementDump
{
    static string S(object o)
    {
        if (o == null || o == DBNull.Value) return "";
        var s = Convert.ToString(o, System.Globalization.CultureInfo.InvariantCulture);
        return s.Replace("\t", " ").Replace("\r", " ").Replace("\n", " ");
    }

    // a collection field's value (a curve, a table): its rows as "col=val;col=val|col=val..."
    static string Coll(object lm)
    {
        try
        {
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            var cols = dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName).ToList();
            return string.Join("|", dv.Cast<System.Data.DataRowView>().Select(r => string.Join(";", cols.Select(c => c + "=" + S(r[c])))));
        }
        catch (Exception ex) { return "ERR:" + ex.GetType().Name; }
    }

    public static void Run(IStormSewerModel m, int scenarioId, string outDir, TextWriter log)
    {
        Directory.CreateDirectory(outDir);
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType();
        var scen = (IScenario)dds.ScenarioManager.Element(scenarioId);
        var types = dst.DomainElementTypes().Cast<IDomainElementType>().ToList();
        var alts = dst.AlternativeTypes().Cast<IAlternativeType>().ToList();
        using (var w = new StreamWriter(Path.Combine(outDir, "elements.tsv"), false, new UTF8Encoding(false)))
        using (var fw = new StreamWriter(Path.Combine(outDir, "fields.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("type_id\ttype\tid\tlabel");
            fw.WriteLine("type_id\ttype\tsource\tfield\tlabel\tid\tvalue");
            foreach (var t in types)
            {
                IDomainElementManager mgr; try { mgr = dds.DomainElementManager(t.Id); } catch { continue; }
                IDictionary labels; try { labels = mgr.ModelingElementField("Label").GetValues(); } catch { continue; }
                if (labels.Count == 0) continue;
                log.WriteLine("type {0} '{1}': {2} elements", t.Id, t.Name, labels.Count);
                foreach (DictionaryEntry e in labels) w.WriteLine(t.Id + "\t" + t.Name + "\t" + e.Key + "\t" + S(e.Value));
                foreach (var at in alts)
                {
                    int altId; try { altId = scen.AlternativeID(at.Id); } catch { continue; }
                    FieldCollection fc; try { fc = dds.FieldManager.AlternativeFields(at.Id, t.Id, altId); } catch { continue; }
                    foreach (IField f in fc)
                    {
                        if (f.FieldDataType == FieldDataType.LongBinary) continue;
                        IDictionary vals; try { vals = f.GetValues(); } catch { continue; }
                        foreach (DictionaryEntry e in vals)
                        {
                            string v = f.FieldDataType == FieldDataType.Collection ? Coll(e.Value) : S(e.Value);
                            if (v == "") continue;
                            fw.WriteLine(t.Id + "\t" + t.Name + "\talt:" + at.Name + "\t" + f.Name + "\t" + S(f.Label) + "\t" + e.Key + "\t" + v);
                        }
                    }
                }
                // results at the first time step, every result record type of this element type
                string eng = ""; try { eng = scen.GetActiveNumericalEngineTypeName("StormSewerResultRecordType"); } catch { }
                if (string.IsNullOrEmpty(eng)) eng = "DelawareProductEngine";
                IEnumerable rrts; try { rrts = t.SupportedResultRecordTypeNames(); } catch { continue; }
                foreach (string rrt in rrts)
                {
                    FieldCollection fc; try { fc = dds.FieldManager.ResultFields(eng, rrt, t.Id); } catch { continue; }
                    foreach (IField f in fc)
                        foreach (DictionaryEntry e in labels)
                        {
                            object v; int id = (int)e.Key;
                            try { var rf = f as IResultTimeVariantField; v = rf != null ? rf.GetValue(id, scenarioId, 0) : f.GetValue(id); }
                            catch { continue; }
                            var sv = S(v); if (sv == "") continue;
                            fw.WriteLine(t.Id + "\t" + t.Name + "\tresult:" + rrt + "\t" + f.Name + "\t" + S(f.Label) + "\t" + id + "\t" + sv);
                        }
                }
            }
        }
        // geometry of every typed element collection of the network (points and polylines/polygons), by reflection
        var ci = System.Globalization.CultureInfo.InvariantCulture;
        using (var g = new StreamWriter(Path.Combine(outDir, "geometry_all.tsv"), false, new UTF8Encoding(false)))
        {
            g.WriteLine("collection\tid\tlabel\tkind\tcoords");
            foreach (var prop in m.Network.GetType().GetProperties())
            {
                object coll; try { coll = prop.GetValue(m.Network, null); } catch { continue; }
                if (coll == null) continue;
                var el = coll.GetType().GetMethod("Elements", Type.EmptyTypes); if (el == null) continue;
                IEnumerable items; try { items = (IEnumerable)el.Invoke(coll, null); } catch { continue; }
                int n = 0;
                foreach (var item in items)
                {
                    n++;
                    var id = item.GetType().GetProperty("Id").GetValue(item, null); var lab = item.GetType().GetProperty("Label").GetValue(item, null);
                    var input = item.GetType().GetProperty("Input").GetValue(item, null);
                    string kind = "", coords = "";
                    foreach (var mn in new[] { "GetPoint", "GetPoints" })
                    {
                        var mi = input.GetType().GetMethod(mn, Type.EmptyTypes); if (mi == null) continue;
                        try
                        {
                            var r = mi.Invoke(input, null);
                            if (r is IEnumerable) coords = string.Join(" ", ((IEnumerable)r).Cast<object>().Select(p => S(p.GetType().GetProperty("X").GetValue(p, null)) + "," + S(p.GetType().GetProperty("Y").GetValue(p, null))));
                            else coords = S(r.GetType().GetProperty("X").GetValue(r, null)) + "," + S(r.GetType().GetProperty("Y").GetValue(r, null));
                            kind = mn; break;
                        }
                        catch { }
                    }
                    g.WriteLine(prop.Name + "\t" + S(id) + "\t" + S(lab) + "\t" + kind + "\t" + coords);
                }
                if (n > 0) log.WriteLine("  network.{0}: {1}", prop.Name, n);
            }
        }
        // the scenario's calculation options (every engine)
        using (var o = new StreamWriter(Path.Combine(outDir, "calc_options.tsv"), false, new UTF8Encoding(false)))
        {
            o.WriteLine("engine\tfield\tlabel\tvalue");
            foreach (INumericalEngineType ne in dst.NumericalEngineTypes())
            {
                try
                {
                    var com = dds.ScenarioManager.CalculationOptionsManager(ne.Name); int cid = scen.CalculationOptionsID(ne.Name);
                    foreach (IField f in com.SupportedFields())
                    {
                        if (f.FieldDataType == FieldDataType.LongBinary) continue;
                        object v; try { v = f.GetValue(cid); } catch { continue; }
                        o.WriteLine(ne.Name + "\t" + f.Name + "\t" + S(f.Label) + "\t" + (f.FieldDataType == FieldDataType.Collection ? Coll(v) : S(v)));
                    }
                }
                catch { }
            }
        }
    }
}
