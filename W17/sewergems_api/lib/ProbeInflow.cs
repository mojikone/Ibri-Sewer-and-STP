using System;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Collections;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class ProbeInflow
{
    public static void Run(IStormSewerModel m, int mhId, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var dst = dds.DomainDataSetType();
        foreach (var pair in new[] { new[] { "InfiltrationAndInflow", "InflowList" }, new[] { "SanitaryLoading", "SanitaryLoads" } })
        {
            int at = dst.AlternativeType(pair[0]).Id;
            int altId = dds.AlternativeManager(at).BaseElements().Cast<IModelingElement>().First().Id;
            var f = dds.FieldManager.AlternativeField(pair[1], at, 1, altId);
            var lm = f.GetValue(mhId);
            log.WriteLine("== {0}.{1} (alt {2}) value type {3}", pair[0], pair[1], altId, lm.GetType().FullName);
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            log.WriteLine("   columns: " + string.Join(" | ", dv.Table.Columns.Cast<System.Data.DataColumn>().Select(c => c.ColumnName + ":" + c.DataType.Name)));
            foreach (var it in new[] { lm.GetType() }.Concat(lm.GetType().GetInterfaces()))
                foreach (var mi in it.GetMethods().Where(x => !x.IsSpecialName && x.DeclaringType == it))
                    log.WriteLine("   M {0}.{1}({2}) : {3}", it.Name, mi.Name, string.Join(", ", mi.GetParameters().Select(p => p.ParameterType.Name + " " + p.Name)), mi.ReturnType.Name);
        }
    }
}
