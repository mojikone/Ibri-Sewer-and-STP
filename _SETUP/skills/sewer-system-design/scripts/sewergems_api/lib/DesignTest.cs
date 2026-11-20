using System;
using System.IO;
using System.Linq;
using System.Collections;
using System.Collections.Generic;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;

public static class DesignTest
{
    public static Dictionary<int, double> Diameters(IStormSewerModel m)
    {
        return m.Network.Conduits.Elements().ToDictionary(c => c.Id, c => c.Input.ConduitDiameter);
    }

    public static void Notes(IStormSewerModel m, int scenarioId, string[] labels, TextWriter log)
    {
        var s = m.Scenarios.Element(scenarioId);
        foreach (var lab in labels)
        {
            var c = m.Network.Conduits.Elements().First(x => x.Label == lab);
            var notes = s.GetUserNotifications(c.Id, 0);
            log.WriteLine("  {0} ({1} mm): {2}", lab, c.Input.ConduitDiameter, notes == null ? "none" : string.Join(" | ", notes.Select(n => n.ToString())));
            foreach (var n in (notes ?? new Haestad.Support.User.IUserNotification[0]).Take(3))
                foreach (var p in n.GetType().GetProperties()) { try { log.WriteLine("      {0} = {1}", p.Name, p.GetValue(n, null)); } catch { } }
        }
    }

    public static void SetDesignSystem(IStormSewerModel m, string field, object value, TextWriter log)
    {
        var dds = m.DomainDataSet;
        var at = dds.DomainDataSetType().AlternativeType("Design");
        var am = dds.AlternativeManager(at.Id);
        var f = (IEditField)am.SystemRecordField(field);
        log.WriteLine("  design {0}: {1} -> {2}", field, f.GetValue(17), value);
        f.SetValue(17, value);
    }
}
