using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

// Colebrook-White friction for gravity pipes (G203 p24, p28: ks = 1.5 mm "shall"; p25 Table 9: nu = 1.141e-6 m2/s at 15 C).
public static class Friction
{
    public const double FT = 0.3048;

    public static void CalcOptions(IStormSewerModel m, int[] calcIds, double nuM2s, TextWriter log)
    {
        var com = m.DomainDataSet.ScenarioManager.CalculationOptionsManager("DelawareProductEngine");
        var fm = (IEditField)com.CalculationOptionsField("HmFrictionMethod");
        var ff = (IEditField)com.CalculationOptionsField("DarcyFrictionFactorMethod");
        var fv = (IEditField)com.CalculationOptionsField("DarcyWeisbachType_KinematicViscosity");
        foreach (int id in calcIds)
        {
            fm.SetValue(id, 2);                       // HmFrictionMethodEnum.DarcyWeisbach
            ff.SetValue(id, 1);                       // DarcyFrictionFactorMethodEnum.ColebrookWhite
            fv.SetValue(id, nuM2s / (FT * FT));       // storage unit ft2/s
            log.WriteLine("  calc options {0}: gravity friction {1}, factor method {2}, viscosity {3:E4} ft2/s ({4:E4} m2/s)", id,
                fm.GetValue(id), ff.GetValue(id), fv.GetValue(id), Convert.ToDouble(fv.GetValue(id)) * FT * FT);
        }
    }

    public static void ConduitRoughness(IStormSewerModel m, int physAltId, double ksMm, TextWriter log)
    {
        var dds = m.DomainDataSet;
        int pt = dds.DomainDataSetType().AlternativeType("Physical").Id;
        var f = (IEditField)dds.FieldManager.AlternativeField("Physical_DarcyWeisbachE", pt, 3, physAltId);
        double e = ksMm / 1000 / FT;
        int n = 0;
        foreach (int id in dds.DomainElementManager(3).ElementIDs()) { f.SetValue(id, e); n++; }
        var vals = f.GetValues(); int ok = 0; foreach (DictionaryEntry v in vals) if (Math.Abs(Convert.ToDouble(v.Value) - e) < 1e-9) ok++;
        log.WriteLine("  physical {0}: Darcy-Weisbach e = {1} mm on {2} conduits ({3} read back)", physAltId, ksMm, n, ok);
    }

    public static void CatalogueRoughness(IStormSewerModel m, double ksMm, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("CatalogConduit");
        var f = (IEditField)dds.FieldManager.SupportElementField("ClassSizeCollection", st.Id);
        double e = ksMm / 1000 / FT;
        foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
        {
            var lm = f.GetValue(el.Id);
            var clm = (ICollectionFieldListManager)lm;
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            var items = dv.Cast<System.Data.DataRowView>().Select(r => Convert.ToInt32(r["ItemID"])).ToList();
            foreach (int it in items) ((IEditField)clm.Field("ClassSizeCollection_DarcyWeisbachE")).SetValue(it, e);
            f.SetValue(el.Id, lm);
            ((IEditField)dds.FieldManager.SupportElementField("ConstantRoughnessType_DarcyWeisbachE", st.Id)).SetValue(el.Id, e);
            log.WriteLine("  catalogue '{0}': Darcy-Weisbach e = {1} mm on {2} sizes (Manning's n left at its value)", el.Label, ksMm, items.Count);
        }
    }
}
