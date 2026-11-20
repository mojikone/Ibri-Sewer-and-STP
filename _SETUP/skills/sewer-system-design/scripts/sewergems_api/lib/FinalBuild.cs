using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using System.Globalization;
using Haestad.Domain;
using Haestad.Support.Support;
using OpenFlows.StormSewer.Domain;
using OpenFlows.StormSewer.Domain.ModelingElements;
using OpenFlows.StormSewer.Domain.ModelingElements.NetworkElements;

// W18 final design (2026-11-18): apply one case of the own design to the model, in the active scenario's alternatives.
// Inputs (py/final_sg_inputs.py), metres: conduits.csv, manholes.csv, outfalls.csv, lifts.csv, joins.csv.
public static class FinalBuild
{
    static readonly CultureInfo CI = CultureInfo.InvariantCulture;
    static double D(string s) { return double.Parse(s, CI); }

    static List<Dictionary<string, string>> Csv(string path)
    {
        var lines = File.ReadAllLines(path); var head = lines[0].Split(',');
        var res = new List<Dictionary<string, string>>();
        foreach (var l in lines.Skip(1))
        {
            if (l.Trim().Length == 0) continue;
            var p = l.Split(','); var d = new Dictionary<string, string>();
            for (int i = 0; i < head.Length; i++) d[head[i]] = i < p.Length ? p[i] : "";
            res.Add(d);
        }
        return res;
    }

    static void Label(object el, string label) { ((IEditLabeled)el).Label = label; }

    public static void Apply(IStormSewerModel m, string dir, TextWriter log)
    {
        var net = m.Network;
        var cat = SizeCheck.Catalogue(m);
        var conduits = net.Conduits.Elements().ToDictionary(c => c.Id);
        var manholes = net.Manholes.Elements().ToDictionary(e => e.Id);
        var outfalls = net.Outfalls.Elements().ToDictionary(e => e.Id);
        // the catalogue entry each size label uses: the one the model's conduits already use, else the first of that label
        var guidOf = new Dictionary<string, Guid>();
        foreach (var c in conduits.Values)
        {
            string k = c.Input.Size.ToString().ToLowerInvariant();
            if (cat.ContainsKey(k) && !guidOf.ContainsKey(cat[k].Item1)) guidOf[cat[k].Item1] = c.Input.Size;
        }
        foreach (var kv in cat) if (!guidOf.ContainsKey(kv.Value.Item1)) guidOf[kv.Value.Item1] = new Guid(kv.Key);

        int n = 0;
        foreach (var r in Csv(Path.Combine(dir, "conduits.csv")))
        {
            var c = conduits[int.Parse(r["id"])]; var i = c.Input;
            i.IsActive = r["active"] == "1";
            i.Size = guidOf[r["size"]];
            i.SetInvertToStart = false; i.SetInvertToStop = false;
            i.StartInvert = D(r["start_inv"]); i.StopInvert = D(r["stop_inv"]);
            Label(c, r["label"]); n++;
        }
        log.WriteLine("  conduits set: {0}", n);
        n = 0;
        foreach (var r in Csv(Path.Combine(dir, "manholes.csv")))
        {
            IManhole h; if (!manholes.TryGetValue(int.Parse(r["id"]), out h)) continue;
            h.Input.InvertElevation = D(r["invert"]); Label(h, r["label"]); n++;
        }
        log.WriteLine("  manholes set: {0}", n);
        n = 0;
        foreach (var r in Csv(Path.Combine(dir, "outfalls.csv")))
        {
            var o = outfalls[int.Parse(r["id"])];
            o.Input.IsActive = r["active"] == "1";
            if (r["invert"] != "" && r["invert"].ToLowerInvariant() != "nan") o.Input.InvertElevation = D(r["invert"]);
            Label(o, r["label"]); n++;
        }
        log.WriteLine("  outfalls set: {0}", n);
        // a lift: its pipe to the next manhole is switched off (conduits.csv); the station manhole drains through a 1 m
        // stub to an outfall 1 m away, and its flow is pumped to the next manhole as a transfer (transfers.csv)
        foreach (var r in Csv(Path.Combine(dir, "lifts.csv")))
        {
            var st = manholes[int.Parse(r["station_id"])]; double x = D(r["x"]), y = D(r["y"]), inv = D(r["invert"]);
            var o = net.Outfalls.Create();
            o.Input.SetPoint(new GeometryPoint(x + 1.0, y)); o.Input.GroundElevation = D(r["ground"]); o.Input.InvertElevation = inv - 0.002;
            Label(o, r["name"] + "-OUT");
            var c = net.Conduits.Create(); var i = c.Input;
            i.StartNode = st; i.StopNode = o;
            i.SetPoints(new List<GeometryPoint> { new GeometryPoint(x, y), new GeometryPoint(x + 1.0, y) });
            i.IsUserDefinedLength = true; i.Length = 1.0; i.Size = guidOf[r["stub_size"]];
            i.SetInvertToStart = false; i.SetInvertToStop = false; i.StartInvert = inv; i.StopInvert = inv - 0.002;
            Label(c, r["name"] + "-ST");
            log.WriteLine("  lift {0}: outfall {1}, stub {2} ({3}, size {4})", r["name"], o.Id, c.Id, c.Input.Length, r["stub_size"]);
        }
        // a gravity join: the joined outfall becomes a manhole, and a new sewer runs to the receiving manhole
        foreach (var r in Csv(Path.Combine(dir, "joins.csv")))
        {
            var oldOf = outfalls[int.Parse(r["outfall_id"])]; double x = D(r["x"]), y = D(r["y"]);
            var h = net.Manholes.Create();
            h.Input.SetPoint(new GeometryPoint(x, y)); h.Input.GroundElevation = D(r["ground"]); h.Input.SetRimToGroundElevation = true;
            h.Input.InvertElevation = D(r["invert"]); Label(h, r["mh_label"]);
            int moved = 0;
            foreach (var c in conduits.Values)                  // a conduit's start/stop need not follow the flow
            {
                if (c.Input.StopNode != null && c.Input.StopNode.Id == oldOf.Id) { c.Input.StopNode = h; moved++; }
                else if (c.Input.StartNode != null && c.Input.StartNode.Id == oldOf.Id) { c.Input.StartNode = h; moved++; }
            }
            oldOf.Input.IsActive = false;
            var rc = manholes[int.Parse(r["receiver_id"])]; var rp = rc.Input.GetPoint();
            var nc = net.Conduits.Create(); var i = nc.Input;
            i.StartNode = h; i.StopNode = rc;
            i.SetPoints(new List<GeometryPoint> { new GeometryPoint(x, y), new GeometryPoint(rp.X, rp.Y) });
            i.IsUserDefinedLength = true; i.Length = D(r["length"]); i.Size = guidOf[r["size"]];
            i.SetInvertToStart = false; i.SetInvertToStop = false; i.StartInvert = D(r["up_inv"]); i.StopInvert = D(r["dn_inv"]);
            Label(nc, r["pipe_label"]);
            log.WriteLine("  join {0}: manhole {1} takes {2} pipes, sewer {3} to {4}", r["mh_label"], h.Id, moved, nc.Id, rc.Label);
        }
    }

    // a read-back of what the model now holds, for the check against the own design
    public static void Check(IStormSewerModel m, string csv, TextWriter log)
    {
        var cat = SizeCheck.Catalogue(m);
        using (var w = new StreamWriter(csv))
        {
            w.WriteLine("id,label,active,size,start_inv,stop_inv,length,start,stop");
            foreach (var c in m.Network.Conduits.Elements())
            {
                var i = c.Input; string k = i.Size.ToString().ToLowerInvariant();
                w.WriteLine(string.Join(",", c.Id, c.Label, i.IsActive, cat.ContainsKey(k) ? cat[k].Item1 : "?", i.StartInvert.ToString(CI),
                    i.StopInvert.ToString(CI), i.Length.ToString(CI), i.StartNode == null ? "" : i.StartNode.Id.ToString(), i.StopNode == null ? "" : i.StopNode.Id.ToString()));
            }
        }
        log.WriteLine("  read-back written: " + csv);
    }
}
