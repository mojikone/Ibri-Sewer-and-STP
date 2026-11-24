"""A SewerGEMS model read directly from its database (the .stsw.sqlite beside the .stsw), with no SewerGEMS.

2026-11-24: the engineer lifted the clean-room rule for this ("now I am asking it. I am the rule"); the risk that
Bentley's licence forbids reading its format was stated and is theirs. The model file is opened read-only (SQLite's
immutable mode: nothing is written, no lock is taken, a model open in SewerGEMS can be read).

What the database holds, as measured on the Ibri SC1-2056 final model against SewerGEMS's own API export of it:
- every value is in Bentley's storage units: feet for lengths, levels and coordinates, cfs for flows;
- each element's values live in tables per kind of data, one row per element and ALTERNATIVE; a child alternative holds
  only what it changes, so a value is the first found walking alternative -> parent -> ... (HMIAlternative.ParentID);
- a scenario names one alternative per alternative type (HMIScenarioAlternative; IsLocal 0: its parent's): 1 geometry,
  2 topology, 3 active topology, 4 physical, 12 sanitary loading;
- geometry is WKB; deleted and prototype elements are flagged in HMIDomainElement; labels are in HMIModelingElement;
- a catalogue pipe's size is its class size (label and inside diameter); the conduit's own typed diameter can be stale;
- sanitary loads are a collection per manhole and alternative (the nearest alternative that has one, whole), unit loads
  times their count, plus pattern base flows; the extreme-flow (peaking) table is a support element.
Results are not in the database (SewerGEMS keeps them in .out files): the app solves the model itself.

export() writes the files of the bridge export (scenarios.csv; conduits_, manholes_, loads_ per scenario; geometry.tsv;
support_loads.csv), so io/sewergems_export.load() opens the model exactly as it opens SewerGEMS's own export.
Pumps and force mains (2026-11-24): SewerGEMS's pump is a node between pressure pipes (the suction from the wet well, the
force main beyond); the app's pump is a link from the wet well to a junction at the pump ("<pump>-out"), from which the
force main's pressure pipes run. Suction pipes and their junctions are inside the station and are left out. Each pump's
definition goes to the pump library (design point, three-point or multiple-point), its on and off elevations become
depths above the wet well's floor; pressure pipes keep their bore, length and Hazen-Williams C (pressure_<file>.csv,
pump_definitions.csv). Not read yet: variable-speed pump batteries, boxes and channels' dimensions."""
import os, sqlite3
import numpy as np, pandas as pd

FT = 0.3048
M3D_PER_CFS = 2446.575545
NODE_KINDS = {"Manhole": "manhole", "Outfall": "outfall", "WetWell": "wetwell", "PressureJunction": "pressure_junction",
              "CatchBasin": "manhole", "JunctionChamber": "manhole", "Pond": "storage", "PondOutletStructure": "storage"}
PUMP_TYPES = {1: "design_point", 2: "three_point", 5: "multi_point"}      # IdahoPumpDefinition.PumpDefinitionType, as stored


def _connect(path):
    p = os.path.abspath(path).replace("\\", "/")
    return sqlite3.connect(f"file:{p}?mode=ro&immutable=1", uri=True)


def _ids(con, table):
    try: return {r[0] for r in con.execute(f'select DomainElementID from "{table}"')}
    except sqlite3.OperationalError: return set()


def _df(con, sql):
    try: return pd.read_sql_query(sql, con)
    except Exception: return pd.DataFrame()


def export(sqlite_path, out, log=None, only=None):
    """Read the model and write the bridge export's files into folder `out`. Returns the scenarios written. only: a set
    of scenario ids to read (tests); every live scenario by default."""
    con = _connect(sqlite_path); os.makedirs(out, exist_ok=True)
    say = log or (lambda s: None)
    A = _df(con, "select AlternativeID, ParentID, AlternativeTypeID from HMIAlternative")
    parent = dict(zip(A.AlternativeID, A.ParentID))

    def chain(a):
        out_, seen = [], set()
        while a is not None and a == a and a not in seen: seen.add(a); out_.append(int(a)); a = parent.get(a)
        return out_
    S = _df(con, "select s.ScenarioID as id, s.ParentID as parent, m.Label as label from HMIScenario s "
                 "left join HMIModelingElement m on m.ElementID = s.ScenarioID where s.IsDeleted = 0 order by s.ScenarioID")
    SA = _df(con, "select ScenarioID, AlternativeTypeID, AlternativeID, IsLocal from HMIScenarioAlternative")
    sa = {(r.ScenarioID, r.AlternativeTypeID): (r.AlternativeID, r.IsLocal) for r in SA.itertuples()}
    spar = dict(zip(S.id, S.parent))
    if only: S = S[S.id.isin(only)]

    def alt(sid, typ, depth=0):
        a, local = sa.get((sid, typ), (None, 1))
        if (a is None or not local) and spar.get(sid) == spar.get(sid) and spar.get(sid) is not None and depth < 50:
            pa = alt(int(spar[sid]), typ, depth + 1)
            if pa is not None: return pa
        return a

    def pick(df, a):
        """Each element's row in the alternative chain of a (the nearest alternative that has one)."""
        if df.empty or a is None: return df.iloc[0:0].set_index("DomainElementID") if "DomainElementID" in df else df
        ch = chain(a); rank = {x: k for k, x in enumerate(ch)}
        d = df[df.AlternativeID.isin(ch)].copy(); d["_r"] = d.AlternativeID.map(rank)
        return d.sort_values("_r").drop_duplicates("DomainElementID").set_index("DomainElementID")

    alive = set(_df(con, "select DomainElementID from HMIDomainElement where IsDeleted = 0 and IsPrototype = 0").DomainElementID)
    alive &= set(_df(con, "select ElementID from HMIModelingElement where IsDeleted = 0").ElementID)
    label = dict(_df(con, "select ElementID, Label from HMIModelingElement").itertuples(index=False, name=None))
    kind = {}
    for t, k in NODE_KINDS.items():
        for i in _ids(con, t) & alive: kind[i] = k
    conduits = _ids(con, "Conduit") & alive
    pumps = _ids(con, "StandardPump") & alive; ppipes = _ids(con, "PressurePipe") & alive
    skipped = {t: len(_ids(con, t) & alive) for t in ("VariableSpeedPumpBattery",)}
    if any(skipped.values()): say(f"  not read yet: {skipped}")

    # the tables, read once; each scenario picks its rows
    ngeo = _df(con, "select DomainElementID, AlternativeID, HMIGeometry from BaseNode_HmiDataSetGeometry_Data")
    nact = _df(con, "select DomainElementID, AlternativeID, HMIActiveTopologyIsActive as on_ from BaseNode_HMIActiveTopology_Data")
    ngr = _df(con, "select DomainElementID, AlternativeID, Physical_GroundElevation as g from BaseNode_Physical_Data")
    ninv = _df(con, "select DomainElementID, AlternativeID, Physical_InvertElevation as inv from GravityNode_Physical_Data")
    ninv2 = _df(con, "select DomainElementID, AlternativeID, Physical_InvertElevation as inv from BaseDirectedNode_Physical_Data")
    ltop = _df(con, "select DomainElementID, AlternativeID, HMITopologyStartNodeID as a, HMITopologyStopNodeID as b from BaseLink_HMIDataSetTopology_Data")
    lgeo = _df(con, "select DomainElementID, AlternativeID, HMIGeometry, HMIGeometryScaledLength as sl from BaseLink_HmiDataSetGeometry_Data")
    lact = _df(con, "select DomainElementID, AlternativeID, HMIActiveTopologyIsActive as on_ from BaseLink_HMIActiveTopology_Data")
    llen = _df(con, "select DomainElementID, AlternativeID, Physical_IsUserDefinedLength as ud, Physical_UserDefinedLength as ul from BaseLink_Physical_Data")
    linv = _df(con, "select DomainElementID, AlternativeID, Physical_SetInvertToUpstream as su, Physical_UpstreamInvert as ui, "
                    "Physical_SetInvertToDownstream as sd, Physical_DownstreamInvert as di from PhysicalLink_Physical_Data")
    lcon = _df(con, "select DomainElementID, AlternativeID, ConduitDiameter as d, ConduitRise as rise, Physical_ConduitShapeLabel as shp, ConduitType as ct from Conduit_Physical_Data")
    lcat = _df(con, "select DomainElementID, AlternativeID, CatalogPipeType_CatalogPipeSize as guid from Conduit_Physical_ConduitType_CatalogConduitType")
    sizes = _df(con, "select ClassSizeCollection_Guid as guid, ClassSizeCollection_Label as lab, ClassSizeCollection_InsideDiameter as d from CatalogConduit_ClassSizeCollection")
    size_lab = dict(zip(sizes.guid, sizes.lab)); size_d = dict(zip(sizes.guid, sizes.d))
    sl_data = _df(con, "select DomainElementID, AlternativeID, SanitaryLoadsCount as n from Manhole_SanitaryLoading_Data")
    sl_rows = _df(con, "select DomainElementID, AlternativeID, SanitaryPatternLoadType_SanitaryBaseFlow as base, "
                       "SanitaryUnitLoadType_UnitSanitaryLoadId as unit, SanitaryUnitLoadType_LoadingUnitNumber as cnt from Manhole_SanitaryLoading_SanitaryLoads")
    unit_cfs = dict(_df(con, "select SupportElementID, UnitSanitaryLoad_UnitLoad from UnitSanitaryLoad").itertuples(index=False, name=None))

    # pumps and force mains
    atype = dict(zip(A.AlternativeID, A.AlternativeTypeID))
    ttype = lambda df: int(atype.get(int(df.AlternativeID.iloc[0]))) if len(df) else None
    dgeo = _df(con, "select DomainElementID, AlternativeID, HMIGeometry from BaseDirectedNode_HmiDataSetGeometry_Data")
    dphy = _df(con, "select DomainElementID, AlternativeID, Physical_GroundElevation as g, Physical_InvertElevation as inv from BaseDirectedNode_Physical_Data")
    dact = _df(con, "select DomainElementID, AlternativeID, HMIActiveTopologyIsActive as on_ from BaseDirectedNode_HMIActiveTopology_Data")
    pjel = _df(con, "select DomainElementID, AlternativeID, Physical_PressureJunctionElevation as el from PressureJunction_Physical_Data")
    wwph = _df(con, "select DomainElementID, AlternativeID, Physical_TankBaseElevation as base, Physical_TankMinimumElevation as mn from WetWell_Physical_Data")
    ppd = _df(con, "select DomainElementID, AlternativeID, Physical_PipeDiameter as d from PressurePipe_Physical_Data")
    pph = _df(con, "select DomainElementID, AlternativeID, Physical_HazenWilliamsC as C, Physical_Material as mat from GravityLinkBase_Physical_Data")
    pmp = _df(con, "select DomainElementID, AlternativeID, Physical_PumpDefinitionID as defid from StandardPump_Physical_Data")
    pop = _df(con, "select DomainElementID, AlternativeID, Operational_OnElevation as on_el, Operational_OffElevation as off_el, Operational_IgnoreOnOffElevations as ign from StandardPump_Operational_Data")
    defs = _df(con, "select SupportElementID as id, PumpDefinitionType as t, DesignDischarge as q, DesignHead as h, ShutoffHead as h0, MaxOperatingDischarge as q2, MaxOperatingHead as h2 from IdahoPumpDefinition")
    curves = _df(con, "select SupportElementID as id, PumpCurve_Discharge as q, PumpCurve_Head as h from IdahoPumpDefinition_PumpCurve order by ItemID")
    used_defs = {}

    def pump_def(i):
        """A pump definition in the app's library form (L/s, m), or None when it holds no usable curve."""
        if i is None or i != i or defs.empty or int(i) not in set(defs.id): return None
        r = defs[defs.id == int(i)].iloc[0]; t = PUMP_TYPES.get(int(r.t)); name = label.get(int(i), f"Pump definition {int(i)}")
        ls, m = lambda v: float(v) * 28.316846592, lambda v: float(v) * FT
        if t == "design_point" and r.q > 0 and r.h > 0: d = dict(name=name, type=t, q_ls=ls(r.q), h_m=m(r.h))
        elif t == "three_point" and r.h0 > r.h > r.h2 >= 0 and r.q2 > r.q > 0:
            d = dict(name=name, type=t, shutoff_h_m=m(r.h0), q_ls=ls(r.q), h_m=m(r.h), max_q_ls=ls(r.q2), max_h_m=m(r.h2))
        elif t == "multi_point":
            pts = [[ls(a), m(b)] for a, b in zip(curves[curves.id == int(i)].q, curves[curves.id == int(i)].h)]
            d = dict(name=name, type=t, points=pts) if len(pts) >= 2 and any(b > 0 for _, b in pts) else None
        elif r.q > 0 and r.h > 0: d = dict(name=name, type="design_point", q_ls=ls(r.q), h_m=m(r.h))
        else: d = None
        if d: used_defs[name] = d
        return d
    from shapely import from_wkb, get_coordinates
    rows_s, geo_written = [], False
    for k, sc in enumerate(S.itertuples(), start=1):
        sid, f = int(sc.id), f"s{k:03d}"
        g1, g2, g3, g4, g12 = (alt(sid, t) for t in (1, 2, 3, 4, 12))
        # structures
        P = pick(ngeo, g1); G = pick(ngr, g4); I = pick(ninv, g4); I2 = pick(ninv2, g4); ACT = pick(nact, g3)
        nodes = []
        for i in sorted(kind):
            if i not in P.index: continue
            xy = get_coordinates(from_wkb(P.HMIGeometry[i]))[0] * FT
            inv = I.inv[i] if i in I.index else (I2.inv[i] if i in I2.index else np.nan)
            nodes.append(dict(id=i, label=label.get(i, str(i)), active=bool(ACT.on_[i]) if i in ACT.index else True, x=xy[0], y=xy[1],
                              ground=G.g[i] * FT if i in G.index else np.nan, rim=G.g[i] * FT if i in G.index else np.nan,
                              invert=inv * FT if inv == inv else np.nan, diameter_m=np.nan if kind[i] == "outfall" else 1.0, kind=kind[i]))
        # pressure junctions and wet wells: their own levels; each pump's outlet: a junction at the pump
        PJ, WW = pick(pjel, alt(sid, ttype(pjel)) if len(pjel) else None), pick(wwph, alt(sid, ttype(wwph)) if len(wwph) else None)
        for r in nodes:
            if r["kind"] == "pressure_junction" and r["id"] in PJ.index: r["invert"] = r["ground"] = PJ.el[r["id"]] * FT
            if r["kind"] == "wetwell" and r["id"] in WW.index:
                b = WW.base[r["id"]] if WW.base[r["id"]] else WW.mn[r["id"]]
                if b: r["invert"] = b * FT
        DG, DP, DA = (pick(t_, alt(sid, ttype(t_)) if len(t_) else None) for t_ in (dgeo, dphy, dact))
        for i in sorted(pumps):
            if i not in DG.index: continue
            xy = get_coordinates(from_wkb(DG.HMIGeometry[i]))[0] * FT
            el = DP.inv[i] * FT if i in DP.index else np.nan
            nodes.append(dict(id=-i, label=f"{label.get(i, i)}-out", active=bool(DA.on_[i]) if i in DA.index else True, x=xy[0], y=xy[1],
                              ground=DP.g[i] * FT if i in DP.index else el, rim=np.nan, invert=el, diameter_m=1.0, kind="pressure_junction"))
        N = pd.DataFrame(nodes)
        ninv_of = dict(zip(N.id, N.invert / FT))
        # pipes
        T = pick(ltop, g2); LG = pick(lgeo, g1); LA = pick(lact, g3); LL = pick(llen, g4); LI = pick(linv, g4); LC = pick(lcon, g4); CA = pick(lcat, g4)
        links, geo = [], []
        for i in sorted(conduits):
            if i not in T.index: continue
            a, b = int(T.a[i]), int(T.b[i])
            line = get_coordinates(from_wkb(LG.HMIGeometry[i])) * FT if i in LG.index and LG.HMIGeometry[i] is not None else None
            length = (LL.ul[i] if i in LL.index and LL.ud[i] else (LG.sl[i] if i in LG.index else np.nan)) * FT
            ui = ninv_of.get(a, np.nan) if i in LI.index and LI.su[i] else (LI.ui[i] if i in LI.index else np.nan)
            di = ninv_of.get(b, np.nan) if i in LI.index and LI.sd[i] else (LI.di[i] if i in LI.index else np.nan)
            guid = CA.guid[i] if i in CA.index else None
            shp = str(LC.shp[i] or "") if i in LC.index else ""
            circ = shp.lower().startswith("circle")
            if guid in size_lab and size_d.get(guid, 0) > 0 and (circ or not shp.strip()):     # the catalogue size decides (a pipe
                lab, dmm = size_lab[guid], size_d[guid] * FT * 1000.0                           # added by the API has no shape label)
            elif circ: lab, dmm = f"{LC.d[i] * FT * 1000.0:.0f} mm", LC.d[i] * FT * 1000.0
            elif i in LC.index and not shp.strip(): lab, dmm = "", LC.d[i] * FT * 1000.0            # no shape named: a circle at its typed bore
            else: lab, dmm = (str(LC.shp[i]) if i in LC.index else "?"), 0.0                    # a box or channel: shown, not analysed
            links.append(dict(id=i, label=label.get(i, str(i)), start=a, stop=b, active=bool(LA.on_[i]) if i in LA.index else True,
                              length_m=length, diameter_mm=dmm, size_label=lab, start_inv=ui * FT, stop_inv=di * FT,
                              flow_m3d=np.nan, velocity_ms=np.nan, depth_in_m=np.nan, depth_out_m=np.nan))
            if not geo_written and line is not None: geo.append(f"{i}\t{label.get(i, i)}\tLINESTRING (" + ", ".join(f"{float(x)!r} {float(y)!r}" for x, y in line[:, :2]) + ")")
        pd.DataFrame(links, columns=["id", "label", "start", "stop", "active", "length_m", "diameter_mm", "size_label", "start_inv", "stop_inv",
                                     "flow_m3d", "velocity_ms", "depth_in_m", "depth_out_m"]).to_csv(os.path.join(out, f"conduits_{f}.csv"), index=False)
        # pumps and force mains: the suction (pressure pipes and junctions from the wet well to the pump) is left out
        if pumps or ppipes:
            PD = pick(ppd, alt(sid, ttype(ppd)) if len(ppd) else None); PH = pick(pph, alt(sid, ttype(pph)) if len(pph) else None)
            PM = pick(pmp, alt(sid, ttype(pmp)) if len(pmp) else None); PO = pick(pop, alt(sid, ttype(pop)) if len(pop) else None)
            stop_of = {i: (int(T.a[i]), int(T.b[i])) for i in ppipes if i in T.index}
            into = {}
            for i, (a, b) in stop_of.items(): into.setdefault(b, []).append(i)
            inv_of = dict(zip(N.id, N.invert)); suction_p, suction_j, prow = set(), set(), []
            for i in sorted(pumps):
                n, src = i, None
                for _ in range(50):                                  # upstream through the suction to the wet well
                    up = into.get(n, [])
                    if not up: break
                    suction_p.add(up[0]); a = stop_of[up[0]][0]
                    if kind.get(a) == "pressure_junction": suction_j.add(a); n = a; continue
                    src = a; break
                d = pump_def(PM.defid[i]) if i in PM.index else None
                base = inv_of.get(src, np.nan)
                on = PO.on_el[i] * FT - base if i in PO.index and PO.on_el[i] and base == base else np.nan
                off = PO.off_el[i] * FT - base if i in PO.index and PO.off_el[i] and base == base else np.nan
                prow.append(dict(id=i, label=label.get(i, str(i)), kind="pump", start=src, stop=-i, active=bool(DA.on_[i]) if i in DA.index else True,
                                 length_m=0.0, diameter_mm=np.nan, C=np.nan, material="", on_m=on if on == on and on > 0 else np.nan,
                                 off_m=off if off == off and off >= 0 else np.nan, definition=d["name"] if d else "", q_ls=d.get("q_ls", np.nan) if d else np.nan))
            for i in sorted(ppipes):
                if i in suction_p or i not in stop_of: continue
                a, b = stop_of[i]; a, b = (-a if a in pumps else a), (-b if b in pumps else b)
                length = (LL.ul[i] if i in LL.index and LL.ud[i] else (LG.sl[i] if i in LG.index else np.nan)) * FT
                prow.append(dict(id=i, label=label.get(i, str(i)), kind="pressure_pipe", start=a, stop=b, active=bool(LA.on_[i]) if i in LA.index else True,
                                 length_m=length, diameter_mm=PD.d[i] * FT * 1000.0 if i in PD.index else np.nan, C=PH.C[i] if i in PH.index else np.nan,
                                 material=PH.mat[i] if i in PH.index else "", on_m=np.nan, off_m=np.nan, definition="", q_ls=np.nan))
            pd.DataFrame(prow).to_csv(os.path.join(out, f"pressure_{f}.csv"), index=False)
            if suction_j: N = N[~N.id.isin(suction_j)]
        N.to_csv(os.path.join(out, f"manholes_{f}.csv"), index=False)
        if not geo_written:
            with open(os.path.join(out, "geometry.tsv"), "w", encoding="utf-8") as fh: fh.write("id\tlabel\twkt\n" + "".join(g + "\n" for g in geo))
            geo_written = True
        # sanitary loads: each manhole's collection in the nearest alternative that has one
        ch = chain(g12) if g12 is not None else []
        if ch and not sl_data.empty:
            rank = {x: j for j, x in enumerate(ch)}
            d = sl_data[sl_data.AlternativeID.isin(ch)].assign(_r=lambda t: t.AlternativeID.map(rank)).sort_values("_r").drop_duplicates("DomainElementID")
            own = set(zip(d.DomainElementID, d.AlternativeID))
            r = sl_rows[[(e, a_) in own and e in kind for e, a_ in zip(sl_rows.DomainElementID, sl_rows.AlternativeID)]].copy()   # live structures only
            r["unit_m3d"] = r.cnt.fillna(0) * r.unit.map(unit_cfs).fillna(0) * M3D_PER_CFS
            r["pattern_m3d"] = r.base.fillna(0) * M3D_PER_CFS
            Ld = r.groupby("DomainElementID").agg(unit_m3d=("unit_m3d", "sum"), pattern_m3d=("pattern_m3d", "sum"),
                                                  unit_load_ids=("unit", lambda s: ";".join(str(int(x)) for x in sorted(set(s.dropna())))))
            Ld = Ld[(Ld.unit_m3d != 0) | (Ld.pattern_m3d != 0)]
            Ld.reset_index().rename(columns={"DomainElementID": "element_id"}).to_csv(os.path.join(out, f"loads_{f}.csv"), index=False)
        rows_s.append(dict(id=sid, label=str(sc.label), parent=int(sc.parent) if sc.parent == sc.parent and sc.parent is not None else 0, file=f))
        say(f"  scenario {sid} '{sc.label}' -> {f}: {len(N)} structures, {len(links)} pipes")
    _support(con, out)
    if used_defs: pd.DataFrame([dict(d, points=";".join(f"{a}:{b}" for a, b in d.get("points", []))) for d in used_defs.values()]).to_csv(os.path.join(out, "pump_definitions.csv"), index=False)
    pd.DataFrame(rows_s).to_csv(os.path.join(out, "scenarios.csv"), index=False)       # last, as the bridge export: the folder is complete
    con.close()
    return rows_s


def _support(con, out):
    """The extreme-flow (peaking) setup and its factor tables, in the bridge export's support_loads.csv form."""
    rows = []
    for r in _df(con, "select * from ExtremeFlowSetup_ExtremeFlowSetupCollection").to_dict("records"):
        v = "|".join(f"{k}={'' if x is None else x}" for k, x in r.items())
        rows.append(dict(type="ExtremeFlowSetup", element_id=r["SupportElementID"], label="", field="ExtremeFlowSetupCollection", value=v))
    curves = _df(con, "select * from ExtremeFlowFactor_EffTableCurve")
    for sid, g in (curves.groupby("SupportElementID") if not curves.empty else []):
        v = " ; ".join("|".join(f"{k}={x}" for k, x in r.items()) for r in g.drop(columns=["ItemID"]).to_dict("records"))
        rows.append(dict(type="ExtremeFlowFactor", element_id=sid, label="", field="EffTableCurve", value=v))
    pd.DataFrame(rows, columns=["type", "element_id", "label", "field", "value"]).to_csv(os.path.join(out, "support_loads.csv"), index=False)
