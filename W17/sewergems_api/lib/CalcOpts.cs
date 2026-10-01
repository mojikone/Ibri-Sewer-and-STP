using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class CalcOpts
{
    public static void Dump(IStormSewerModel m, string engine, TextWriter log)
    {
        var com = m.DomainDataSet.ScenarioManager.CalculationOptionsManager(engine);
        var ids = com.Elements().Cast<IModelingElement>().ToList();
        log.WriteLine("field | " + string.Join(" | ", ids.Select(e => e.Id + ":" + e.Label)));
        foreach (IField f in com.SupportedFields())
        {
            var vals = ids.Select(e => { try { return Convert.ToString(f.GetValue(e.Id)); } catch { return "?"; } }).ToList();
            log.WriteLine("{0} | {1}{2}", f.Name, string.Join(" | ", vals), vals.Distinct().Count() > 1 ? "   <-- differs" : "");
        }
    }
}
