using System;
using System.IO;
using System.Linq;
using System.Text;
using System.Collections.Generic;
using Haestad.Domain;
using OpenFlows.StormSewer.Domain;
using Haestad.Support.Support;

// W19 (2026-11-22): the cross-section of every conduit that is not a circle, for the app's box and open-channel hydraulics.
// Shape, rise, span, bottom width and side slopes come from the conduit's catalogue size (class + GUID, as B4 reads it;
// lengths stored in feet); Manning's n from the conduit. Then SewerGEMS's own results of the active scenario for the same
// conduits (flow, velocity, depths, normal and critical depth, full capacity), converted to m3/s and metres by factors
// measured on the model itself (see Snap), whatever its display units. Circular conduits are left out.
public static class Sections
{
    static readonly System.Globalization.CultureInfo CI = System.Globalization.CultureInfo.InvariantCulture;
    static readonly string[] RES = { "Flow", "Velocity", "DepthIn", "DepthOut", "NormalDepth", "CriticalDepth", "FullFlowCapacity" };   // normal and critical depth: GVF fields below
    class Row { public double Rise, Span, Bottom, ZL, ZR; public string ClassLabel, Label, CatShape; }

    static double D(object v) { try { return v == null || v == DBNull.Value ? double.NaN : Convert.ToDouble(v, CI); } catch { return double.NaN; } }
    static string S(double v) { return double.IsNaN(v) || double.IsInfinity(v) ? "" : v.ToString("R", CI); }
    static string Q(string s) { s = s ?? ""; return s.Contains(",") || s.Contains("\"") ? "\"" + s.Replace("\"", "\"\"") + "\"" : s; }

    static Dictionary<string, Row> Catalogue(IStormSewerModel m)
    {
        var dds = m.DomainDataSet;
        var st = dds.DomainDataSetType().SupportElementType("CatalogConduit");
        var f = dds.FieldManager.SupportElementField("ClassSizeCollection", st.Id);
        var fs = dds.FieldManager.SupportElementField("CatalogConduitShape", st.Id);
        var res = new Dictionary<string, Row>();
        foreach (IModelingElement el in dds.SupportElementManager(st.Id).Elements())
        {
            string cshape = ""; try { cshape = Convert.ToString(fs.GetValue(el.Id), CI); } catch { }
            var lm = f.GetValue(el.Id);
            var dv = (System.Data.DataView)lm.GetType().GetProperty("DataView").GetValue(lm, null);
            foreach (System.Data.DataRowView r in dv)
                res[el.Id + ":" + Convert.ToString(r["ClassSizeCollection_Guid"]).ToLowerInvariant()] = new Row {
                    Rise = D(r["ClassSizeCollection_Rise"]) * 0.3048, Span = D(r["ClassSizeCollection_Span"]) * 0.3048,
                    Bottom = D(r["ClassSizeCollection_BottomWidth"]) * 0.3048,
                    ZL = D(r["ClassSizeCollection_LeftSideSlope"]), ZR = D(r["ClassSizeCollection_RightSideSlope"]),
                    ClassLabel = el.Label, Label = Convert.ToString(r["ClassSizeCollection_Label"]), CatShape = cshape };
        }
        return res;
    }

    static Dictionary<string, IField> Gvf(IStormSewerModel m, int scenarioId)
    {
        var res = new Dictionary<string, IField>();
        try
        {
            var dds = m.DomainDataSet; var sc = (IScenario)dds.ScenarioManager.Element(scenarioId);
            string eng = "DelawareProductEngine";
            try { var e = sc.GetActiveNumericalEngineTypeName("StormSewerResultRecordType"); if (!string.IsNullOrEmpty(e)) eng = e; } catch { }
            foreach (IField f in dds.FieldManager.ResultFields(eng, "GVFConduitResults", 3))
                if (f.Name == "GVFConduitResults_NormalDepth" || f.Name == "GVFConduitResults_CriticalDepth") res[f.Name] = f;
        }
        catch { }
        return res;
    }
    static double G(Dictionary<string, IField> gvf, string name, int id, int scenarioId)
    {
        IField f; if (!gvf.TryGetValue(name, out f)) return double.NaN;
        try { var tv = f as IResultTimeVariantField; return D(tv != null ? tv.GetValue(id, scenarioId, 0) : f.GetValue(id)) * 0.3048; }
        catch { return double.NaN; }
    }

    static double R(object results, string name)
    {
        if (results == null) return double.NaN;
        try { var mi = results.GetType().GetMethod(name, Type.EmptyTypes); if (mi == null) return double.NaN; return D(mi.Invoke(results, null)); }
        catch { return double.NaN; }
    }

    // The display units of the typed values, measured rather than assumed: a length factor from the catalogue rise (stored
    // in feet) against the conduit's displayed rise, a flow factor from Manning's flow at the full section (SI, from the
    // catalogue's dimensions, n and the slope) against SewerGEMS's displayed full capacity. Each is snapped to the nearest
    // common unit (m3/s, L/s, m3/h, m3/d, cfs, gpm, MGD; m, ft, mm, in) within 25 %, else NaN (left out of the file).
    static readonly double[] FLOWS = { 1, 0.001, 1 / 3600.0, 1 / 86400.0, 0.028316846592, 6.30901964e-5, 0.0438126364 };
    static readonly double[] LENGTHS = { 1, 0.3048, 0.001, 0.0254 };
    static double Snap(List<double> ratios, double[] units)
    {
        var r = ratios.Where(x => x > 0 && !double.IsNaN(x) && !double.IsInfinity(x)).OrderBy(x => x).ToList();
        if (r.Count == 0) return double.NaN;
        double med = r[r.Count / 2];
        var best = units.OrderBy(u => Math.Abs(Math.Log(med / u))).First();
        return Math.Abs(Math.Log(med / best)) < Math.Log(1.25) ? best : double.NaN;
    }
    static double FullManning(string code, double rise, double span, double bottom, double zl, double zr, double n, double S)
    {
        if (!(S > 0) || !(n > 0) || !(rise > 0)) return double.NaN;
        double A, P;
        if (code == "box") { A = span * rise; P = 2 * (span + rise); }
        else if (code == "rect_open") { A = span * rise; P = span + 2 * rise; }
        else { A = bottom * rise + 0.5 * (zl + zr) * rise * rise; P = bottom + rise * (Math.Sqrt(1 + zl * zl) + Math.Sqrt(1 + zr * zr)); }
        return A * Math.Pow(A / P, 2.0 / 3.0) * Math.Sqrt(S) / n;
    }
    static string Code(string shape)
    {
        return shape.IndexOf("Box", StringComparison.OrdinalIgnoreCase) >= 0 ? "box"
            : shape.IndexOf("Trap", StringComparison.OrdinalIgnoreCase) >= 0 ? "trapezoid"
            : shape.IndexOf("Rect", StringComparison.OrdinalIgnoreCase) >= 0 ? "rect_open" : shape;
    }

    public static void Export(IStormSewerModel m, string csv, TextWriter log)
    {
        var cat = Catalogue(m); var cls = B4.ConduitClasses(m);
        var items = new List<Tuple<IConduit, Row, string>>();
        var lr = new List<double>(); var fr = new List<double>();
        foreach (var c in m.Network.Conduits.Elements())
        {
            var i = c.Input; string shape = Convert.ToString(i.ConduitShape);
            if (shape.IndexOf("Circ", StringComparison.OrdinalIgnoreCase) >= 0) continue;
            Row row = null; int classId; string key = i.Size == null ? "" : i.Size.ToString().ToLowerInvariant();
            if (key != "" && cls.TryGetValue(c.Id, out classId)) cat.TryGetValue(classId + ":" + key, out row);
            items.Add(Tuple.Create(c, row, Code(shape)));
            if (row != null && row.Rise > 0 && i.ConduitRise > 0) lr.Add(row.Rise / i.ConduitRise);
        }
        double lengthToM = Snap(lr, LENGTHS);
        if (double.IsNaN(lengthToM)) lengthToM = 1.0;          // no catalogue rows to measure against: metres assumed
        foreach (var it in items)
        {
            var i = it.Item1.Input; var row = it.Item2; double L = i.Length * lengthToM;
            double rise = row != null && row.Rise > 0 ? row.Rise : i.ConduitRise * lengthToM, span = row != null && row.Span > 0 ? row.Span : i.ConduitSpan * lengthToM;
            double q = FullManning(it.Item3, rise, span, row != null ? row.Bottom : 0, row != null ? row.ZL : 0, row != null ? row.ZR : 0, i.ManningsN,
                L > 0 ? (i.StartInvert - i.StopInvert) * lengthToM / L : double.NaN);
            fr.Add(q / R(B4.Res(it.Item1), "FullFlowCapacity"));
        }
        double flowToM3s = Snap(fr, FLOWS);
        log.WriteLine("  section units: length x{0}, flow x{1} (to m and m3/s)", lengthToM.ToString("R", CI), double.IsNaN(flowToM3s) ? "unknown" : flowToM3s.ToString("R", CI));
        int n = 0, box = 0, open = 0, other = 0;
        using (var w = new StreamWriter(csv, false, new UTF8Encoding(false)))
        {
            int sid = m.ActiveScenario.Id; var gvf = Gvf(m, sid);
            w.WriteLine("id,label,shape,rise_m,span_m,bottom_m,z_left,z_right,n,barrels,class_label,size_label,catalogue_shape,flow_m3s,velocity_ms,depth_in_m,depth_out_m,normal_depth_m,critical_depth_m,full_capacity_m3s");
            foreach (var it in items)
            {
                var c = it.Item1; var i = c.Input; var row = it.Item2; string code = it.Item3;
                double rise = row != null && row.Rise > 0 ? row.Rise : i.ConduitRise * lengthToM;
                double span = row != null && row.Span > 0 ? row.Span : i.ConduitSpan * lengthToM;
                if (code == "box") box++; else if (code == "trapezoid" || code == "rect_open") open++; else other++;
                var res = B4.Res(c);
                var v = RES.Select(x => R(res, x)).ToArray();
                int nb = 1; try { nb = Math.Max(1, i.NumberOfBarrels); } catch { }
                w.WriteLine(string.Join(",", c.Id, Q(c.Label), Q(code), S(rise), S(span), S(row != null ? row.Bottom : double.NaN),
                    S(row != null ? row.ZL : double.NaN), S(row != null ? row.ZR : double.NaN), S(i.ManningsN), nb,
                    Q(row != null ? row.ClassLabel : ""), Q(row != null ? row.Label : ""), Q(row != null ? row.CatShape : ""),
                    S(v[0] * flowToM3s), S(v[1] * lengthToM), S(v[2] * lengthToM), S(v[3] * lengthToM),
                    S(G(gvf, "GVFConduitResults_NormalDepth", c.Id, sid)), S(G(gvf, "GVFConduitResults_CriticalDepth", c.Id, sid)), S(v[6] * flowToM3s)));
                n++;
            }
        }
        log.WriteLine("  {0} non-circular sections written ({1} box, {2} open channel, {3} other shapes)", n, box, open, other);
    }
}
