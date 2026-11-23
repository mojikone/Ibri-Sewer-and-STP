using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// W19 (2026-11-23): SewerGEMS's own data model, as the installed program declares it through the API: every domain
// element type, every alternative type with the input fields it holds per element type, every numerical engine with its
// calculation-option fields, every support element type (pump definitions, unit loads, patterns, storm data...) with
// its fields, and the result fields per engine and element type. Read only; any model opens it.
public static class DomainCatalogue
{
    static string S(object o) { return o == null ? "" : Convert.ToString(o, System.Globalization.CultureInfo.InvariantCulture).Replace("\t", " ").Replace("\n", " ").Replace("\r", " "); }

    public static void Run(IStormSewerModel m, string outDir, TextWriter log)
    {
        Directory.CreateDirectory(outDir);
        var dds = m.DomainDataSet; var dst = dds.DomainDataSetType(); var fm = dds.FieldManager;
        var types = dst.DomainElementTypes().Cast<IDomainElementType>().ToList();
        var alts = dst.AlternativeTypes().Cast<IAlternativeType>().ToList();
        using (var w = new StreamWriter(Path.Combine(outDir, "element_types.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("type_id\tname\tlabel\tresult_record_types");
            foreach (var t in types)
            {
                string rr = ""; try { rr = string.Join("|", t.SupportedResultRecordTypeNames().Cast<string>()); } catch { }
                w.WriteLine(t.Id + "\t" + S(t.Name) + "\t" + S(t.Label) + "\t" + rr);
            }
        }
        log.WriteLine("element types: " + types.Count);
        using (var w = new StreamWriter(Path.Combine(outDir, "input_fields.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("alternative_type\talt_label\telement_type\tfield\tlabel\tdata_type\tunit");
            foreach (var at in alts)
            {
                int baseAlt; try { baseAlt = ((IAlternative)dds.AlternativeManager(at.Id).Elements().Cast<object>().First()).Id; } catch { continue; }
                foreach (var t in types)
                {
                    FieldCollection fc; try { fc = fm.AlternativeFields(at.Id, t.Id, baseAlt); } catch { continue; }
                    foreach (IField f in fc)
                    {
                        string u = "";
                        w.WriteLine(S(at.Name) + "\t" + S(at.Label) + "\t" + S(t.Name) + "\t" + S(f.Name) + "\t" + S(f.Label) + "\t" + f.FieldDataType + "\t" + u);
                    }
                }
            }
        }
        using (var w = new StreamWriter(Path.Combine(outDir, "calc_option_fields.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("engine\tfield\tlabel\tdata_type");
            foreach (INumericalEngineType ne in dst.NumericalEngineTypes())
            {
                try
                {
                    var com = dds.ScenarioManager.CalculationOptionsManager(ne.Name);
                    foreach (IField f in com.SupportedFields()) w.WriteLine(S(ne.Name) + "\t" + S(f.Name) + "\t" + S(f.Label) + "\t" + f.FieldDataType);
                }
                catch (Exception ex) { w.WriteLine(S(ne.Name) + "\t(" + ex.GetType().Name + ")\t\t"); }
            }
        }
        using (var w = new StreamWriter(Path.Combine(outDir, "support_types.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("support_type_id\tname\tlabel\tfield\tfield_label\tdata_type");
            foreach (ISupportElementType st in dst.SupportElementTypes())
            {
                bool any = false;
                try
                {
                    var mgr = dds.SupportElementManager(st.Id);
                    foreach (IField f in mgr.SupportedFields()) { any = true; w.WriteLine(st.Id + "\t" + S(st.Name) + "\t" + S(st.Label) + "\t" + S(f.Name) + "\t" + S(f.Label) + "\t" + f.FieldDataType); }
                }
                catch { }
                if (!any) w.WriteLine(st.Id + "\t" + S(st.Name) + "\t" + S(st.Label) + "\t\t\t");
            }
        }
        using (var w = new StreamWriter(Path.Combine(outDir, "result_fields.tsv"), false, new UTF8Encoding(false)))
        {
            w.WriteLine("engine\telement_type\trecord_type\tfield\tlabel");
            foreach (INumericalEngineType ne in dst.NumericalEngineTypes())
                foreach (var t in types)
                {
                    IEnumerable rr; try { rr = t.SupportedResultRecordTypeNames(); } catch { continue; }
                    foreach (string r in rr)
                    {
                        FieldCollection fc; try { fc = fm.ResultFields(ne.Name, r, t.Id); } catch { continue; }
                        foreach (IField f in fc) w.WriteLine(S(ne.Name) + "\t" + S(t.Name) + "\t" + r + "\t" + S(f.Name) + "\t" + S(f.Label));
                    }
                }
        }
        log.WriteLine("alternative types: " + alts.Count + "; engines: " + dst.NumericalEngineTypes().Count);
    }
}
