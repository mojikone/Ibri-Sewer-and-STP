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
Not read yet: pumps and pressure pipes (counted in the log), boxes and channels' dimensions (shown, not analysed)."""
import os, sqlite3
import numpy as np, pandas as pd

FT = 0.3048
M3D_PER_CFS = 2446.575545
NODE_KINDS = {"Manhole": "manhole", "Outfall": "outfall", "WetWell": "wetwell", "PressureJunction": "pressure_junction",
              "CatchBasin": "manhole", "JunctionChamber": "manhole"}


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
    skipped = {t: len(_ids(con, t) & alive) for t in ("StandardPump", "VariableSpeedPumpBattery", "PressurePipe")}
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
        N = pd.DataFrame(nodes); N.to_csv(os.path.join(out, f"manholes_{f}.csv"), index=False)
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
        pd.DataFrame(links).to_csv(os.path.join(out, f"conduits_{f}.csv"), index=False)
        if not geo_written:
            with open(os.path.join(out, "geometry.tsv"), "w", encoding="utf-8") as fh: fh.write("id\tlabel\twkt\n" + "\n".join(geo) + "\n")
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
