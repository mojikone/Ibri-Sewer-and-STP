using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class SizeCheck
{
    // Catalogue size GUID -> label and inside diameter (mm).
    public static Dictionary<string, Tuple<string, double>> Catalogue(IStormSewerModel m)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("CatalogConduit");
        var f = dds.FieldManager.SupportElementField("ClassSizeCollection", st.Id);
        var res = new Dictionary<string, Tuple<string, double>>();
        foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
        {
            var lm = f.GetValue(el.Id);
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            foreach (System.Data.DataRowView r in dv)
                res[Convert.ToString(r["ClassSizeCollection_Guid"]).ToLowerInvariant()] = Tuple.Create(Convert.ToString(r["ClassSizeCollection_Label"]), Convert.ToDouble(r["ClassSizeCollection_InsideDiameter"]) * 304.8);
        }
        return res;
    }

    // Per conduit: catalogue size and diameter field in two physical alternatives.
    public static void Compare(IStormSewerModel m, int altA, int altB, string csv, TextWriter log)
    {
        var dds = m.DomainDataSet; var fm = dds.FieldManager;
        int pt = dds.DomainDataSetType().AlternativeType("Physical").Id;
        var cat = Catalogue(m);
        var labels = dds.DomainElementManager(3).ModelingElementField("Label").GetValues();
        var ga = fm.AlternativeField("CatalogPipeType_CatalogPipeSize", pt, 3, altA).GetValues();
        var gb = fm.AlternativeField("CatalogPipeType_CatalogPipeSize", pt, 3, altB).GetValues();
        var da = fm.AlternativeField("ConduitDiameter", pt, 3, altA).GetValues();
        var db = fm.AlternativeField("ConduitDiameter", pt, 3, altB).GetValues();
        int sizeChanged = 0, diaChanged = 0;
        using (var w = new StreamWriter(csv))
        {
            w.WriteLine("id,label,size_a,size_b,id_a_mm,id_b_mm,diameter_field_a_mm,diameter_field_b_mm");
            foreach (DictionaryEntry e in ga)
            {
                string a = Convert.ToString(e.Value).ToLowerInvariant(), b = Convert.ToString(gb[e.Key]).ToLowerInvariant();
                double fa = Convert.ToDouble(da[e.Key]) * 304.8, fb = Convert.ToDouble(db[e.Key]) * 304.8;
                if (a != b) sizeChanged++;
                if (Math.Abs(fa - fb) > 1e-3) diaChanged++;
                Tuple<string, double> ca, cb; cat.TryGetValue(a, out ca); cat.TryGetValue(b, out cb);
                w.WriteLine("{0},{1},{2},{3},{4},{5},{6},{7}", e.Key, labels[e.Key], ca == null ? a : ca.Item1, cb == null ? b : cb.Item1,
                    ca == null ? 0 : ca.Item2, cb == null ? 0 : cb.Item2, fa, fb);
            }
        }
        log.WriteLine("  physical {0} vs {1}: catalogue size changed on {2} pipes, diameter field changed on {3}", altA, altB, sizeChanged, diaChanged);
    }
}
