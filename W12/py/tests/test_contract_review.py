"""ADVERSARIAL REVIEW OF THE CONTRACT CHANGES OF 2026-09-06.

Three things the contract change did that its own report did not name, each written as the
check that would have caught it.

1. WIDENING AN ENUM DEFANGED A GUARD IN ANOTHER FILE. `s8_export` ends its self-test with
   `ck("SRC map lands only on contract values", set(SRC_MAP.values()) <= set(CT.SRC))` and
   the same for CONF_MAP. Those two lines exist to prove the COLLAPSE happened - that the
   deliverable no longer carries s1's private spellings. The moment `draft_base`,
   `draft_propo` and `corroborated` were added to `contract.SRC` / `contract.CONFIDENCE`,
   an IDENTITY map - no collapse at all - satisfies them. The check went on printing a
   tick while measuring nothing. The right target is the DELIVERABLE set, and until
   s8_export is edited these tests hold the line from outside it.

2. THE COLLAPSE IS NOT ONE MAPPING. The contract declared `SRC_EXPORT` and
   `CONFIDENCE_EXPORT` as "the collapse, declared once" and told s6 and s8 to read them.
   s8's real rule is those two tables PLUS `SRC_CONF_FLOOR {draft_propo -> provisional}`,
   and s6's is a different table again. Adopting the contract's pair as written would have
   dropped the floor - the half P6 is actually about. Measured: the two stages already
   publish different grades for 14,536 of the 56,521 reaches they share.

3. THE MANIFEST NEVER APPENDED. `Manifest.save` wrote only the records made in the current
   process, and every stage runs in its own subprocess, so run/manifest.json held ONE
   stage after an eight-stage run.

Every number here is measured in the test body or read from `w12.contract`; none is typed
from the report being reviewed.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest

from conftest import SHP_DIR


# ======================================================================================
# 1. the widening must not have weakened anything downstream
# ======================================================================================

def test_the_deliverable_vocabulary_is_strictly_smaller_than_the_enum(contract):
    """If the two sets were equal, every guard written as `<= set(CT.SRC)` would be
    vacuous and nothing would notice. They are not equal BECAUSE the enum was widened, and
    that is precisely why the deliverable sets have to exist and be used."""
    assert set(contract.SRC_DELIVERABLE) < set(contract.SRC)
    assert set(contract.CONFIDENCE_DELIVERABLE) < set(contract.CONFIDENCE)
    assert not (set(contract.SRC_EXPORT) & set(contract.SRC_DELIVERABLE))
    assert not (set(contract.CONFIDENCE_EXPORT) & set(contract.CONFIDENCE_DELIVERABLE))


def test_the_stage_collapse_tables_land_inside_the_deliverable_set(contract):
    """THE GUARD s8_export LOST. Its own line reads `set(SRC_MAP.values()) <= set(CT.SRC)`,
    which an identity map now satisfies. Asserted here against SRC_DELIVERABLE /
    CONFIDENCE_DELIVERABLE, which an identity map cannot satisfy, for BOTH stages that keep
    a private copy of the mapping.

    This is the standing check until s8_export.py:6408-6410 and s6_levels are pointed at
    the deliverable sets themselves."""
    import s6_levels
    import s8_export

    for mod, name in ((s6_levels, "s6_levels"), (s8_export, "s8_export")):
        src_vals = set(mod.SRC_MAP.values())
        conf_vals = set(mod.CONF_MAP.values())
        leaked_src = sorted(src_vals - set(contract.SRC_DELIVERABLE))
        leaked_conf = sorted(conf_vals - set(contract.CONFIDENCE_DELIVERABLE))
        print(f"\n    [{name}] SRC map -> {sorted(src_vals)}; CONFIDENCE map -> "
              f"{sorted(conf_vals)}")
        assert not leaked_src, (
            f"{name}.SRC_MAP still lands on the upstream spelling {leaked_src}. That is the "
            "collapse not happening, and since `draft_*` joined contract.SRC the stage's "
            "own `<= set(CT.SRC)` check can no longer see it.")
        assert not leaked_conf, (
            f"{name}.CONF_MAP still lands on {leaked_conf}, which is an upstream grade.")
        # every upstream token the contract names must have somewhere to go, or the stage
        # silently passes it through with a .get() default
        for tok in contract.SRC_EXPORT:
            assert tok in mod.SRC_MAP, (
                f"{name}.SRC_MAP has no entry for '{tok}'. The stage reads its map with a "
                "default, so a missing entry is a silent substitution, not an error.")


def test_no_upstream_token_reaches_the_client_deliverable(contract):
    """The other direction, measured on the package the client receives rather than on the
    mapping that is supposed to produce it."""
    fiona = pytest.importorskip("fiona")
    import geopandas as gpd
    p = SHP_DIR / "W12_export.gpkg"
    if not p.is_file():
        pytest.skip("stage 8 has not published W12_export.gpkg")
    seen = 0
    for name in fiona.listlayers(str(p)):
        g = gpd.read_file(str(p), layer=name)
        if "SRC" not in g.columns and "CONFIDENCE" not in g.columns:
            continue
        seen += 1
        contract.assert_export_vocabulary(g, f"export/{name}")
    assert seen, "no deliverable layer carried a provenance column"
    print(f"\n    [deliverable] {seen} layer(s) checked against the "
          f"{len(contract.SRC_DELIVERABLE)}-token SRC and "
          f"{len(contract.CONFIDENCE_DELIVERABLE)}-token CONFIDENCE export sets")


# ======================================================================================
# 2. the collapse is two tables and a floor, and the two stages do not agree
# ======================================================================================

def test_the_floor_is_declared_and_is_not_expressible_as_a_token_table(contract):
    """`SRC_CONFIDENCE_FLOOR` is the half of the collapse a token-for-token map cannot
    carry: the grade a row may not beat GIVEN ITS SOURCE. It has to be checkable against
    the raw source, so the gate reads SRC_RAW."""
    import geopandas as gpd
    from shapely.geometry import Point

    assert contract.SRC_CONFIDENCE_FLOOR, "the floor must be declared, not implied"
    assert set(contract.SRC_CONFIDENCE_FLOOR) <= set(contract.SRC)

    def row(**kw):
        return gpd.GeoDataFrame([kw], geometry=[Point(0.0, 0.0)], crs=contract.CRS_EPSG)

    for src, floor in contract.SRC_CONFIDENCE_FLOOR.items():
        better = [c for c in contract.CONFIDENCE
                  if contract._CONF_RANK[c] < contract._CONF_RANK[floor]]
        assert better, f"'{floor}' is already the worst grade; the floor would be a no-op"
        with pytest.raises(contract.ContractError):
            contract.assert_export_vocabulary(
                row(SRC="dwg_road", SRC_RAW=src, CONFIDENCE=better[-1]), "exported")
        contract.assert_export_vocabulary(
            row(SRC="dwg_road", SRC_RAW=src, CONFIDENCE=floor), "exported")


@pytest.mark.published
def test_the_export_floor_cannot_be_audited_because_the_raw_source_is_dropped(contract):
    """A FINDING HELD OPEN, not a passing check. s8_export computes `segments['SRC_RAW']`
    and then does not publish it, so on the deliverable there is nothing left to test the
    floor against: every row reads `dwg_road` whether it came from the base road set or the
    draftsman's proposed streets. The floor IS applied - s8 notes how many rows it floored -
    but the client's package cannot be checked for it, and philosophy sec 8 makes a check
    that cannot run a failure rather than a blank.

    Written as a test so it is counted rather than remembered. It passes the day
    s8_export publishes SRC_RAW on the layers that carry SRC."""
    fiona = pytest.importorskip("fiona")
    import geopandas as gpd
    p = SHP_DIR / "W12_export.gpkg"
    if not p.is_file():
        pytest.skip("stage 8 has not published W12_export.gpkg")
    blind = []
    for name in fiona.listlayers(str(p)):
        g = gpd.read_file(str(p), layer=name)
        if "SRC" not in g.columns:
            continue
        if "SRC_RAW" not in g.columns:
            blind.append(f"{name} ({len(g):,} rows)")
    assert not blind, (
        "these deliverable layers carry SRC but not SRC_RAW, so "
        f"{contract.SRC_CONFIDENCE_FLOOR} cannot be verified on the package the client "
        "receives: " + ", ".join(blind) + ". s8_export already computes SRC_RAW on its "
        "segments; publishing it costs one column and makes the P6 floor auditable.")


@pytest.mark.published
def test_the_two_stages_still_disagree_and_the_contract_still_says_so():
    """The conflict record must not go stale in either direction: if the stages are
    reconciled the record must be deleted, and while they are not it must stand.

    Measured here, not quoted."""
    fiona = pytest.importorskip("fiona")
    import geopandas as gpd
    from w12 import contract as K

    a_p, b_p = SHP_DIR / "W12.gpkg", SHP_DIR / "W12_export.gpkg"
    if not (a_p.is_file() and b_p.is_file()):
        pytest.skip("both reach layers are needed to compare the two collapses")
    if "reaches" not in fiona.listlayers(str(a_p)) or \
            "reaches" not in fiona.listlayers(str(b_p)):
        pytest.skip("no reaches layer to compare")
    a = gpd.read_file(str(a_p), layer="reaches")
    b = gpd.read_file(str(b_p), layer="reaches")
    if "CONFIDENCE" not in a.columns or "CONFIDENCE" not in b.columns:
        pytest.skip("no CONFIDENCE column to compare")
    ka = a.set_index([a.US_NODE.astype(str), a.DS_NODE.astype(str)])["CONFIDENCE"]
    kb = b.set_index([b.US_NODE.astype(str), b.DS_NODE.astype(str)])["CONFIDENCE"]
    j = ka.to_frame("s6").join(kb.to_frame("s8"), how="inner")
    n_diff = int((j.s6 != j.s8).sum())
    print(f"\n    [collapse] {len(j):,} reaches appear in both published layers; "
          f"{n_diff:,} ({100.0 * n_diff / max(len(j), 1):.1f} %) carry a different "
          f"CONFIDENCE. s6 stricter on {int(((j.s6 == 'provisional') & (j.s8 != 'provisional')).sum()):,}, "
          f"s8 stricter on {int(((j.s8 == 'provisional') & (j.s6 != 'provisional')).sum()):,}.")
    if n_diff == 0:
        pytest.fail(
            "the two stages now agree, so contract.STAGE_VOCABULARY_CONFLICT is stale and "
            "must be deleted - a conflict record that outlives its conflict is how a "
            "reader is sent looking for a problem that is fixed.")
    assert "UNRESOLVED" in K.STAGE_VOCABULARY_CONFLICT
    assert "s6_levels" in K.STAGE_VOCABULARY_CONFLICT
    assert "s8_export" in K.STAGE_VOCABULARY_CONFLICT


# ======================================================================================
# 3. the manifest
# ======================================================================================

def test_the_manifest_survives_a_stage_running_in_its_own_process(contract):
    """Every stage is a separate subprocess, so `Manifest.records` starts empty each time.
    A save that writes only that list truncates the ledger to the last stage to finish -
    which is what run/manifest.json held: one of eight."""
    K = contract
    keep = K.Manifest.records
    try:
        path = os.path.join(tempfile.mkdtemp(), "manifest.json")
        for name, order in (("s3_hierarchy", 3), ("s8_export", 8), ("s1_roads", 1)):
            K.Manifest.records = []                      # what a new process starts with
            with K.Manifest.stage(name, order, path=path) as rec:
                rec.wrote("demo", path, order)
        got = K.Manifest.load(path)
        assert [s["stage"] for s in got] == ["s1_roads", "s3_hierarchy", "s8_export"], (
            f"the ledger holds {[s['stage'] for s in got]} - a stage was lost, which is the "
            "defect that made audit check G4 unanswerable")
        assert all(s.get("written") for s in got), (
            "a merged record without its own timestamp can pass for part of this run when "
            "it is left over from an older one")
        # a re-run replaces one stage and leaves the rest alone
        K.Manifest.records = []
        with K.Manifest.stage("s3_hierarchy", 3, path=path) as rec:
            rec.wrote("demo", path, 99)
        got = K.Manifest.load(path)
        assert len(got) == 3
        assert [s for s in got if s["stage"] == "s3_hierarchy"][0]["writes"][0]["n"] == 99
        # and the file is valid JSON a reader can open
        with open(path, encoding="utf-8") as fh:
            assert len(json.load(fh)["stages"]) == 3
    finally:
        K.Manifest.records = keep


def test_a_stage_that_writes_nothing_must_still_say_so(contract):
    """The rule the merge must not weaken: a stage may do nothing, it may not do nothing
    quietly. Kept here because `save()` changed underneath it."""
    K = contract
    keep = K.Manifest.records
    try:
        path = os.path.join(tempfile.mkdtemp(), "manifest.json")
        K.Manifest.records = []
        with pytest.raises(K.ContractError, match="wrote nothing"):
            with K.Manifest.stage("s_quiet", 4, path=path):
                pass
        K.Manifest.records = []
        with K.Manifest.stage("s_honest", 4, path=path) as rec:
            rec.did_nothing("nothing to do: no corridor changed since the last run")
        got = K.Manifest.load(path)
        assert got and got[0]["no_change_reason"]
    finally:
        K.Manifest.records = keep


@pytest.mark.published
def test_how_many_stages_register_with_the_manifest_at_all():
    """The merge fixes the truncation. It does not invent records for stages that never
    call `Manifest.stage`, and five of the eight do not - reported here so the fix is not
    mistaken for the ledger being complete."""
    import re
    py = SHP_DIR.parent / "py"
    stages = sorted(p for p in py.glob("s?_*.py"))
    if not stages:
        pytest.skip("no stage modules found")
    registers, silent = [], []
    for p in stages:
        txt = p.read_text(encoding="utf-8", errors="replace")
        (registers if re.search(r"Manifest\.stage\(", txt) else silent).append(p.stem)
    print(f"\n    [manifest] {len(registers)} of {len(stages)} stages register a record: "
          f"{registers}. Silent: {silent}")
    assert registers, "no stage registers with the manifest at all"
