"""End-to-end tests of the general network editor (web/editor) in system Chrome against a live server on port 8798."""
import os, re, subprocess, sys, time, urllib.request
import pytest
from playwright.sync_api import sync_playwright, expect

W19 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PORT = 8798
URL = f"http://127.0.0.1:{PORT}"
M_LON, M_LAT = 111319.49, 110574.0          # local-metre projects: degrees <-> metres (api/coords.py)
EXTRAN1 = os.path.join(W19, "tests", "fixtures", "swmm", "extran", "extran1.inp")
SHOTS = os.path.join(W19, "work")


@pytest.fixture(scope="module")
def sg_exports(tmp_path_factory):
    """A SewerGEMS export folder laid out as bridge job 100 writes it (two scenarios), from the frozen W18 referee run."""
    from sewerapp import fixtures
    root = tmp_path_factory.mktemp("sg_exports"); d = root / "SC1-2056_final"; d.mkdir()
    fixtures.materialize("sewergems/SC1-2056/conduits_SC1-2056.csv", str(d / "conduits_s001.csv"))
    fixtures.materialize("sewergems/SC1-2056/conduits_SC1-2056-at-2031.csv", str(d / "conduits_s002.csv"))
    for f in ("s001", "s002"): fixtures.materialize("sewergems/SC1-2056/manholes_SC1-2056.csv", str(d / f"manholes_{f}.csv"))
    (d / "scenarios.csv").write_text('id,label,parent,file\n1,"SC1-2056 design",0,s001\n2,"SC1-2056 design at the 2031 peak",1,s002\n')
    return str(root)


@pytest.fixture(scope="module")
def server(sg_exports):
    p = subprocess.Popen([sys.executable, "-c", "import uvicorn; uvicorn.run('sewerapp.api.app:app', host='127.0.0.1', port=8798)"],
                         cwd=W19, env=dict(os.environ, W19_ASSISTANT_STUB="1", W19_SG_EXPORTS=sg_exports), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while True:
            try:
                urllib.request.urlopen(URL + "/api/g/samples", timeout=2); break
            except Exception:
                if p.poll() is not None: raise RuntimeError("server exited")
                if time.time() - t0 > 120: raise RuntimeError("server did not start")
                time.sleep(0.5)
        yield URL
    finally:
        p.terminate()
        try: p.wait(10)
        except Exception: p.kill()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        yield b
        b.close()


@pytest.fixture(scope="module")
def page(server, browser):
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}, accept_downloads=True)
    pg = ctx.new_page(); pg.set_default_timeout(60000); pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(server + "/static/editor/index.html")
    pg.wait_for_function("window.ed && window.ed.map")
    yield pg
    ctx.close()


# ------------------------------------------------------------------ helpers
def idle(pg):
    pg.evaluate("window.ed.idle()")
    pg.wait_for_function("document.body.dataset.pending === '0'")


def ll(x, y): return [x / M_LON, y / M_LAT]


def click_at(pg, x, y):
    pg.evaluate("([lon, lat]) => window.ed.clickAt(lon, lat)", ll(x, y))


def tool(pg, name): pg.get_by_test_id("tool-" + name).click()


def file_menu(pg, item):
    """File actions live in the File menu: open it, then click the item."""
    pg.get_by_test_id("file-btn").click(); pg.get_by_test_id(item).click()


def new_local(pg, name="Test"):
    file_menu(pg, "new-btn")
    pg.get_by_test_id("new-name").fill(name)
    pg.get_by_test_id("new-crs-mode").select_option("local")
    pg.get_by_test_id("new-create").click()
    pg.wait_for_function("window.ed.state.pid && window.ed.state.model && document.body.dataset.pending === '0'")
    pg.evaluate("window.ed.map.jumpTo({center: [150 / 111319.49, 0], zoom: 17})")
    pg.wait_for_function("window.ed.map.loaded() || true")


def set_prop(pg, field, value):
    el = pg.get_by_test_id("prop-" + field)
    el.fill(str(value)); el.press("Enter"); idle(pg)


def ids(pg, table):
    return pg.evaluate(f"[...window.ed.state.model.{table}.keys()]")


NODES = [("manhole", 0, 100.0, 98.0), ("manhole", 100, 99.5, 97.5), ("manhole", 200, 99.0, 97.0), ("outfall", 300, 98.5, 96.5)]


def draw_network(pg, dn=None, levels=True):
    """Three manholes and an outfall drawn with the toolbar, joined by three pipes; levels typed in the property grid."""
    new_local(pg)
    for kind, x, _, _ in NODES:
        tool(pg, kind); click_at(pg, x, 0)
    idle(pg)
    nid = ids(pg, "nodes"); assert len(nid) == 4
    tool(pg, "pipe")
    for a, b in ((0, 100), (100, 200), (200, 300)):
        click_at(pg, a, 0); click_at(pg, b, 0)
    idle(pg)
    assert len(ids(pg, "links")) == 3
    if levels:
        tool(pg, "select")
        for n, (_, _, g, i) in zip(nid, NODES):
            pg.evaluate("([t, i]) => window.ed.selectElement(t, i)", ["nodes", n])
            set_prop(pg, "ground", g); set_prop(pg, "invert", i)
        pg.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
        ld = pg.get_by_test_id("load-design"); ld.fill("86.4"); ld.press("Enter"); idle(pg)
    if dn:
        for l in ids(pg, "links"):
            pg.evaluate("id => window.ed.selectElement('links', id)", l); pg.get_by_test_id("prop-dn_mm").select_option(str(dn)); idle(pg)
    return nid, ids(pg, "links")


def status(pg): return pg.evaluate("document.getElementById('status-line').dataset")


def summary(pg): return pg.evaluate("window.ed.state.summary")


def result(pg, lid, key): return pg.evaluate("([l, k]) => window.ed.state.results.links[l][k]", [lid, key])


# ------------------------------------------------------------------ tests
def test_draw_network_with_the_toolbar_and_solve(page):
    nid, lid = draw_network(page)
    st = status(page)
    assert st["links"] == "3" and st["problems"] == "0", st
    assert "solved 3 links" in page.get_by_test_id("status-line").inner_text()
    page.get_by_test_id("tab-results").click()
    row = page.locator('#tbl-results tr[data-id="%s"]' % lid[-1])
    expect(row).to_have_count(1)
    cols = page.locator("#tbl-results thead th").all_inner_texts()
    v = float(row.locator("td").nth(cols.index("v_ms")).inner_text())
    assert v > 0, v
    assert result(page, lid[-1], "v_ms") > 0
    # a screenshot of the drawn network with its property grid
    page.get_by_test_id("tab-links").click()
    page.evaluate("id => window.ed.selectElement('links', id)", lid[1])
    page.evaluate("window.ed.map.jumpTo({center: [150 / 111319.49, 0], zoom: 17.3})"); page.wait_for_timeout(600)
    os.makedirs(SHOTS, exist_ok=True); page.screenshot(path=os.path.join(SHOTS, "screenshot_editor.png"))


def test_bulk_edit_two_pipes_in_the_links_table(page):
    nid, lid = draw_network(page)
    rev = int(status(page)["rev"])
    page.get_by_test_id("tab-links").click()
    page.locator('#tbl-links tr[data-id="%s"]' % lid[0]).click()
    page.locator('#tbl-links tr[data-id="%s"]' % lid[1]).click(modifiers=["Control"])
    assert page.evaluate("window.ed.state.sel.ids.length") == 2
    page.get_by_test_id("bulk-field-links").select_option("dn_mm")
    page.get_by_test_id("bulk-value-links").select_option("315")
    page.get_by_test_id("bulk-apply-links").click(); idle(page)
    cols = page.locator("#tbl-links thead th").all_inner_texts()
    for l in lid[:2]:
        assert page.locator('#tbl-links tr[data-id="%s"] td' % l).nth(cols.index("dn_mm")).inner_text() == "315"
        assert result(page, l, "dn_mm") == 315
    assert result(page, lid[2], "dn_mm") == 200
    assert int(status(page)["rev"]) > rev


def test_undo_and_redo_a_pipe_edit(page):
    nid, lid = draw_network(page)
    page.evaluate("id => window.ed.selectElement('links', id)", lid[1])
    page.get_by_test_id("prop-dn_mm").select_option("400"); idle(page)
    assert result(page, lid[1], "dn_mm") == 400
    expect(page.get_by_test_id("undo-btn")).to_be_enabled()
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert result(page, lid[1], "dn_mm") == 200
    expect(page.get_by_test_id("redo-btn")).to_be_enabled()
    page.get_by_test_id("redo-btn").click(); idle(page)
    assert result(page, lid[1], "dn_mm") == 400


def test_split_a_pipe_and_delete_a_node(page):
    nid, lid = draw_network(page)
    tool(page, "manhole"); click_at(page, 150, 0); idle(page)           # on the second pipe, away from any node
    assert page.evaluate("window.ed.counts()") == {"nodes": 5, "links": 4}
    assert set(ids(page, "links")) >= {lid[1] + "-a", lid[1] + "-b"}
    tool(page, "delete"); click_at(page, 100, 0); idle(page)             # MH at x = 100 and its two links
    c = page.evaluate("window.ed.counts()")
    assert c["nodes"] == 4 and c["links"] == 2, c


def test_save_and_open_a_project_file(page, tmp_path):
    draw_network(page)
    before = page.evaluate("window.ed.counts()"); pid = page.evaluate("window.ed.state.pid")
    with page.expect_download() as d:
        page.get_by_test_id("save-btn").click()
    f = str(tmp_path / "saved.gpkg"); d.value.save_as(f)
    assert d.value.suggested_filename.endswith(".gpkg") and os.path.getsize(f) > 10_000
    page.set_input_files("#open-file", f)
    page.wait_for_function("p => window.ed.state.pid !== p && window.ed.state.model && document.body.dataset.pending === '0'", arg=pid)
    assert page.evaluate("window.ed.counts()") == before


def test_ibri_sample_opens_copies_and_resolves_fast(page):
    file_menu(page, "sample-btn")
    page.get_by_test_id("sample-SC1-2056").click()
    page.wait_for_function("window.ed.state.pid && window.ed.state.model && window.ed.state.model.linkFeat.length > 19000 && document.body.dataset.pending === '0'", timeout=180000)
    assert int(status(page)["links"]) >= 19083
    page.wait_for_timeout(1500)
    page.screenshot(path=os.path.join(SHOTS, "screenshot_editor_ibri.png"))
    sid0 = page.evaluate("window.ed.state.sid")
    page.get_by_test_id("copy-btn").click(); idle(page)
    assert page.evaluate("window.ed.state.sid") != sid0
    page.evaluate("window.ed.selectElement('links', 'P1-P151')")
    page.get_by_test_id("prop-dn_mm").select_option("1200"); idle(page)
    assert summary(page)["seconds"] < 2.0, summary(page)
    assert result(page, "P1-P151", "dn_mm") == 1200 and not result(page, "P1-P151", "over_limit")
    assert int(status(page)["links"]) >= 19083


def test_profile_tab_draws_the_long_section(page):
    nid, lid = draw_network(page)
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
    page.get_by_test_id("tab-profile").click()
    expect(page.locator("#profile-svg .seg")).to_have_count(3)
    assert page.locator("#profile-svg text").filter(has_text="Chainage").count() == 1


def test_settings_friction_method_changes_velocities(page):
    nid, lid = draw_network(page)
    v0 = result(page, lid[2], "v_ms")
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("set-friction.method").select_option("manning"); idle(page)
    assert page.evaluate("window.ed.state.model.settings.friction.method") == "manning"
    v1 = result(page, lid[2], "v_ms")
    assert v1 != v0 and v1 > 0, (v0, v1)


def test_checks_and_design_tools_with_undo(page):
    nid, lid = draw_network(page)
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
    ld = page.get_by_test_id("load-design"); ld.fill("5000"); ld.press("Enter"); idle(page)
    assert summary(page)["over_limit"] > 0
    dn0 = page.evaluate("Object.values(window.ed.state.results.links).map(r => r.dn_mm)")
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-checks").click(); idle(page)
    expect(page.get_by_test_id("tab-toolout")).to_have_class("tab active")
    n = page.locator("#tbl-toolout tbody tr").count(); assert n > 0
    page.locator("#tbl-toolout tbody tr").first.click()
    assert page.evaluate("window.ed.state.sel.table") == "links"
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-design").click(); idle(page)
    assert summary(page)["over_limit"] == 0, summary(page)
    dn1 = page.evaluate("Object.values(window.ed.state.results.links).map(r => r.dn_mm)")
    assert dn1 != dn0
    expect(page.get_by_test_id("design-report")).to_be_visible()
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert page.evaluate("Object.values(window.ed.state.results.links).map(r => r.dn_mm)") == dn0
    assert summary(page)["over_limit"] > 0


def draw_storm_network(pg):
    nid, lid = draw_network(pg, dn=630)
    tool(pg, "catchment")
    for x, y in ((-40, 20), (-40, 120), (60, 120), (60, 20)):
        click_at(pg, x, y)
    pg.evaluate("window.ed.finish()")
    click_at(pg, 0, 0); idle(pg)                                         # the outlet: the first manhole
    assert len(ids(pg, "catchments")) == 1
    return nid, lid


def test_catchment_rain_and_storm_run_with_hydrograph(page):
    nid, lid = draw_storm_network(page)
    cid = ids(page, "catchments")[0]
    p = page.evaluate("id => window.ed.state.model.catchments.get(id).properties", cid)
    assert abs(p["area_ha"] - 100 * 100 / 1e4) < 0.05 and p["outlet"] == nid[0] and p["imperv_pc"] == 50
    # a storm with no rain says so
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-storm").click(); idle(page)
    expect(page.get_by_test_id("toast")).to_contain_text("rain")
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("rain-step").fill("5"); page.get_by_test_id("rain-duration").fill("30")
    for i, (d, q) in enumerate(((5, 140), (15, 90), (30, 62), (60, 40))):
        page.get_by_test_id("rain-add-row").click()
        page.get_by_test_id(f"rain-row-{i}-a").fill(str(d)); page.get_by_test_id(f"rain-row-{i}-b").fill(str(q))
    page.get_by_test_id("rain-apply").click(); idle(page)
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-storm").click(); idle(page)
    expect(page.get_by_test_id("storm-report")).to_be_visible()
    assert page.locator('[data-testid="storm-report"] b[data-k="subcatchments"]').inner_text() == "1"
    peak = page.evaluate("l => window.ed.state.storm.data.links[l].q_peak", lid[2]); assert peak > 0
    # colour by storm results, the legend follows
    assert page.evaluate("window.ed.state.colorBy") == "storm_cap"
    # hydrograph of the last pipe
    page.evaluate("id => window.ed.selectElement('links', id)", lid[2])
    page.get_by_test_id("tab-hydro").click()
    expect(page.locator("#hydro-svg polyline.curve")).to_have_count(1)
    pts = page.locator("#hydro-svg polyline.curve").get_attribute("points").split()
    assert len(pts) > 10
    # and the catchment's runoff
    page.evaluate("id => window.ed.selectElement('catchments', id)", cid)
    page.get_by_test_id("hydro-attr").select_option("runoff_rate")
    expect(page.locator("#hydro-svg polyline.curve")).to_have_count(1)


def test_import_swmm_inp_run_storm_and_export(page, tmp_path):
    pid = page.evaluate("window.ed.state.pid")
    page.set_input_files("#import-file", EXTRAN1)
    page.wait_for_function("p => window.ed.state.pid !== p && window.ed.state.model && document.body.dataset.pending === '0'", arg=pid)
    assert page.evaluate("window.ed.counts()") == {"nodes": 10, "links": 9}
    assert page.evaluate("window.ed.state.info.basemap") is False
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-storm").click(); idle(page)
    expect(page.get_by_test_id("storm-report")).to_be_visible()
    assert page.evaluate("window.ed.state.storm.data.summary.links") == 9
    with page.expect_download() as d:
        file_menu(page, "export-btn")
    f = str(tmp_path / "model.inp"); d.value.save_as(f)
    assert "[CONDUITS]" in open(f, encoding="utf-8", errors="ignore").read()


def test_assistant_answers_with_a_tool_call_and_rain_follows_the_model(page):
    nid, lid = draw_network(page)
    page.get_by_test_id("tab-assistant").click()
    expect(page.get_by_test_id("asst-input")).to_be_enabled()
    page.get_by_test_id("asst-input").fill("Which pipes fail the checks?")
    page.get_by_test_id("asst-send").click(); idle(page)
    expect(page.get_by_test_id("asst-reply")).to_contain_text("over the d/D limit")
    expect(page.get_by_test_id("asst-tool")).to_have_count(1)
    expect(page.get_by_test_id("asst-tool")).to_contain_text("project_summary")
    assert "tokens" in page.get_by_test_id("asst-usage").inner_text()
    assert page.evaluate("window.ed.state.history.length") == 2
    # the Rain form is filled from the scenario's own rain: apply, undo, and the form follows
    page.get_by_test_id("tab-settings").click()
    page.get_by_test_id("rain-add-row").click()
    page.get_by_test_id("rain-row-0-a").fill("10"); page.get_by_test_id("rain-row-0-b").fill("100")
    page.get_by_test_id("rain-apply").click(); idle(page)
    assert page.evaluate("window.ed.state.model.rain.idf.durations_min") == [10]
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert page.evaluate("window.ed.state.rain.idf.length") == 0
    expect(page.locator("#rain-row-0-a")).to_have_count(0)


def test_open_a_sewergems_export_and_read_its_stored_results(page):
    from sewerapp import fixtures
    file_menu(page, "sg-btn")
    page.get_by_test_id("sg-SC1-2056_final").click()
    page.wait_for_function("window.ed.state.pid && window.ed.state.info.name.startsWith('SewerGEMS') && window.ed.state.model && window.ed.state.model.linkFeat.length > 19000 && document.body.dataset.pending === '0'", timeout=240000)
    opts = page.get_by_test_id("scenario-select").locator("option").all_inner_texts()
    assert opts == ["SC1-2056 design", "SC1-2056 design at the 2031 peak"], opts
    assert page.evaluate("window.ed.state.source") == "engine"
    page.get_by_test_id("results-source").select_option("stored"); idle(page)
    assert "SewerGEMS" in page.get_by_test_id("results-src").inner_text()
    page.evaluate("window.ed.selectElement('links', 'P1-P1')")
    q1 = float(page.get_by_test_id("res-q_ls").inner_text()); assert q1 > 0
    sg = fixtures.read_csv("sewergems/SC1-2056/conduits_SC1-2056.csv").set_index("label")
    assert abs(q1 - sg.flow_m3d["P1-P1"] / 86.4) < 1e-3
    assert "sewergems" in page.get_by_test_id("prop-grid").inner_text().lower()
    assert "Velocity" in page.get_by_test_id("legend").inner_text()
    sid2 = page.evaluate("window.ed.state.info.scenarios[1].id")
    page.get_by_test_id("scenario-select").select_option(sid2); idle(page)
    page.evaluate("window.ed.selectElement('links', 'P1-P1')")
    q2 = float(page.get_by_test_id("res-q_ls").inner_text())
    assert 0 < q2 < q1, (q1, q2)                                          # the 2031 peak is below the design year
    expect(page.get_by_test_id("undo-btn")).to_be_disabled()             # the model's own scenario is not an undoable edit
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-compare_stored").click(); idle(page)
    expect(page.get_by_test_id("tab-toolout")).to_have_class("tab active")
    assert int(page.locator('[data-k="links"]').first.inner_text()) > 19000
    assert "flows within 0.1 % of SewerGEMS" in page.get_by_test_id("design-report").inner_text()
    # a narrower window with a long project name: the toolbar wraps, the property grid stays on screen
    page.set_viewport_size({"width": 1280, "height": 800})
    try:
        page.wait_for_timeout(300)
        w = page.evaluate("[document.documentElement.scrollWidth, innerWidth, document.getElementById('props').getBoundingClientRect().right]")
        assert w[0] == w[1] and w[2] <= w[1] + 0.5, w
    finally:
        page.set_viewport_size({"width": 1600, "height": 950})
    page.get_by_test_id("results-source").select_option("engine"); idle(page)
    assert page.evaluate("window.ed.state.source") == "engine"


def test_stored_results_are_disabled_for_a_plain_project(page):
    draw_network(page)
    assert page.get_by_test_id("results-source").locator("option[value=stored]").is_disabled()
    page.get_by_test_id("tools-btn").click()
    expect(page.get_by_test_id("tool-run-compare_stored")).to_have_count(0)
    page.get_by_test_id("tools-btn").click()


def _gis_layers(tmp):
    """The two GeoPackages of tests/general/test_gate_g5.py::_network (foreign field names, P3's ends 0.4 m off)."""
    import geopandas as gpd
    from shapely.geometry import LineString, Point
    n = gpd.GeoDataFrame(dict(MH_ID=["A", "B", "C", "OUT"], GL=[100.0, 99.5, 99.0, 98.5], IL=[98.0, 97.4, 96.8, 96.2],
                              TYPE=["manhole", "manhole", "manhole", "outfall"]),
                         geometry=[Point(0, 0), Point(100, 0), Point(200, 0), Point(300, 0)], crs=32640)
    l = gpd.GeoDataFrame(dict(PIPE=["P1", "P2", "P3"], DIA=[200, 250, 315]),
                         geometry=[LineString([(0, 0), (100, 0)]), LineString([(100, 0), (150, 10), (200, 0)]),
                                   LineString([(200, 0.4), (300, -0.3)])], crs=32640)
    fn, fl = os.path.join(tmp, "nodes.gpkg"), os.path.join(tmp, "links.gpkg"); n.to_file(fn); l.to_file(fl)
    return fn, fl


def _gis_dialog(page, fn, fl, snap):
    page.get_by_test_id("file-btn").click(); page.get_by_test_id("gis-btn").click()
    page.set_input_files("#gis-nodes-file", fn); page.set_input_files("#gis-links-file", fl)
    expect(page.get_by_test_id("gis-map-nodes-ground")).to_be_visible()
    expect(page.get_by_test_id("gis-map-links-dn_mm")).to_be_visible()
    for f, v in (("id", "MH_ID"), ("kind", "TYPE"), ("ground", "GL"), ("invert", "IL")):
        page.get_by_test_id(f"gis-map-nodes-{f}").select_option(v)
    for f, v in (("id", "PIPE"), ("dn_mm", "DIA")):
        page.get_by_test_id(f"gis-map-links-{f}").select_option(v)
    page.get_by_test_id("gis-snap").fill(str(snap))
    page.get_by_test_id("gis-import").click()


def test_import_from_gis_layers_with_mapping_snapping_and_exports(page, tmp_path):
    fn, fl = _gis_layers(str(tmp_path))
    new_local(page)                                                       # something is open already
    _gis_dialog(page, fn, fl, 0.1)                                        # too tight: P3's ends are 0.4 m off
    expect(page.get_by_test_id("gis-error")).to_contain_text("tolerance")
    page.get_by_test_id("gis-snap").fill("1.0"); pid = page.evaluate("window.ed.state.pid")
    page.get_by_test_id("gis-import").click()
    page.wait_for_function("p => window.ed.state.pid !== p && window.ed.state.model && document.body.dataset.pending === '0'", arg=pid)
    assert page.evaluate("window.ed.counts()") == {"nodes": 4, "links": 3}
    p3 = page.evaluate("window.ed.state.model.links.get('P3').properties")
    assert (p3["from_node"], p3["to_node"], p3["dn_mm"]) == ("C", "OUT", 315)
    assert page.evaluate("window.ed.state.info.basemap") is True
    for btn, ext, marker in (("export-dxf-btn", ".dxf", None), ("export-csv-btn", ".csv", "v_ms")):
        page.get_by_test_id("file-btn").click()
        with page.expect_download() as d:
            page.get_by_test_id(btn).click()
        f = str(tmp_path / ("out" + ext)); d.value.save_as(f)
        assert d.value.suggested_filename.endswith(ext) and os.path.getsize(f) > 100
        if marker: assert marker in open(f, encoding="utf-8", errors="ignore").read().splitlines()[0]


def test_panels_collapse_drag_and_are_remembered(page):
    draw_network(page)
    body = page.locator("body")
    page.keyboard.press("F2"); expect(body).to_have_class(re.compile("props-collapsed"))
    assert page.evaluate("document.getElementById('props').getBoundingClientRect().width") <= 31
    page.keyboard.press("F2"); expect(body).not_to_have_class(re.compile("props-collapsed"))
    page.get_by_test_id("bottom-toggle").click(); expect(body).to_have_class(re.compile("bottom-collapsed"))
    page.get_by_test_id("tab-links").click(); expect(body).not_to_have_class(re.compile("bottom-collapsed"))  # a tab re-opens it
    # drag the bottom splitter up by 120 px: the tables grow by 120 px, the map shrinks, and the size is stored
    h0 = page.evaluate("document.getElementById('bottom').getBoundingClientRect().height")
    m0 = page.evaluate("document.getElementById('map-wrap').getBoundingClientRect().height")
    b = page.get_by_test_id("split-bottom").bounding_box()
    page.mouse.move(b["x"] + 200, b["y"] + 3); page.mouse.down(); page.mouse.move(b["x"] + 200, b["y"] - 117, steps=6); page.mouse.up()
    page.wait_for_timeout(200)
    h1 = page.evaluate("document.getElementById('bottom').getBoundingClientRect().height")
    m1 = page.evaluate("document.getElementById('map-wrap').getBoundingClientRect().height")
    assert abs((h1 - h0) - 120) < 4 and abs((m0 - m1) - 120) < 4, (h0, h1, m0, m1)
    assert abs(page.evaluate("JSON.parse(localStorage.getItem('w19.ui')).bh") - h1) < 2
    # the properties splitter: drag left by 100 px
    w0 = page.evaluate("document.getElementById('props').getBoundingClientRect().width")
    b = page.get_by_test_id("split-props").bounding_box()
    page.mouse.move(b["x"] + 3, b["y"] + 100); page.mouse.down(); page.mouse.move(b["x"] - 97, b["y"] + 100, steps=6); page.mouse.up()
    page.wait_for_timeout(200)
    assert abs(page.evaluate("document.getElementById('props').getBoundingClientRect().width") - w0 - 100) < 4
    page.get_by_test_id("maxmap-btn").click(); expect(body).to_have_class(re.compile("props-collapsed"))
    expect(body).to_have_class(re.compile("bottom-collapsed"))
    page.get_by_test_id("maxmap-btn").click(); expect(body).not_to_have_class(re.compile("bottom-collapsed"))
    page.evaluate("localStorage.removeItem('w19.ui')")


def test_find_measure_coordinates_and_failure_stepping(page):
    nid, lid = draw_network(page)
    page.get_by_test_id("find-input").fill(nid[1].lower()); page.get_by_test_id("find-input").press("Enter"); idle(page)
    assert page.evaluate("window.ed.state.sel") == {"table": "nodes", "ids": [nid[1]]}
    tool(page, "measure"); click_at(page, 0, 0); click_at(page, 100, 0); idle(page)
    assert abs(page.evaluate("window.ed.state.measureLength") - 100) < 0.01           # local metres: 100 m between the clicks, in plan
    assert "Length 100" in page.get_by_test_id("hint").inner_text()
    page.keyboard.press("Escape"); assert page.evaluate("window.ed.state.measure.length") == 0
    page.evaluate(f"showCoords({{lng: 150 / {M_LON}, lat: 40 / {M_LAT}}})")
    assert page.get_by_test_id("coords").text_content().startswith("E 150.0  N 40.0")
    tool(page, "select")
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
    ld = page.get_by_test_id("load-design"); ld.fill("5000"); ld.press("Enter"); idle(page)
    n = summary(page)["over_limit"]; assert n > 0
    first = page.locator('#status-line a.fail[data-flag="over_limit"]'); first.click(); idle(page)
    s1 = page.evaluate("window.ed.state.sel.ids[0]"); assert page.evaluate("id => window.ed.state.results.links[id].over_limit", s1)
    if n > 1:
        page.locator('#status-line a.fail[data-flag="over_limit"]').click(); idle(page)
        assert page.evaluate("window.ed.state.sel.ids[0]") != s1


def test_basemaps_hillshade_theme_and_utm_readout(page):
    file_menu(page, "new-btn"); page.get_by_test_id("new-name").fill("Basemap"); page.get_by_test_id("new-crs-mode").select_option("epsg")
    page.get_by_test_id("new-epsg").fill("32640"); page.get_by_test_id("new-create").click()
    page.wait_for_function("window.ed.state.pid && window.ed.state.info.name === 'Basemap' && document.body.dataset.pending === '0'")
    vis = lambda l: page.evaluate("l => window.ed.map.getLayoutProperty(l, 'visibility')", l)
    page.get_by_test_id("basemap-select").select_option("sat")
    assert vis("bm-sat") == "visible" and vis("bm-osm") == "none" and vis("sat-labels") == "visible"
    page.get_by_test_id("labels-toggle").uncheck(); assert vis("sat-labels") == "none"
    page.get_by_test_id("hillshade-toggle").check(); assert vis("hillshade") == "visible"
    page.get_by_test_id("basemap-opacity").fill("0.5")
    assert page.evaluate("window.ed.map.getPaintProperty('bm-sat', 'raster-opacity')") == 0.5
    page.get_by_test_id("theme-btn").click(); expect(page.locator("body")).to_have_class(re.compile("dark"))
    page.get_by_test_id("basemap-select").select_option("osm")
    page.get_by_test_id("theme-btn").click(); expect(page.locator("body")).not_to_have_class(re.compile("dark"))
    # the E/N readout's UTM formula against PROJ, inside zone 40N and near its edge
    from pyproj import Transformer
    T = Transformer.from_crs(4326, 32640, always_xy=True)
    for lon, lat in ((56.4567, 23.1756), (59.9, 16.0), (54.1, 26.3)):
        e, n = page.evaluate("([lon, lat]) => utm(lon, lat, 40, false)", [lon, lat]); pe, pn = T.transform(lon, lat)
        assert abs(e - pe) < 0.01 and abs(n - pn) < 0.01, (lon, lat, e - pe, n - pn)
    page.evaluate("localStorage.removeItem('w19.ui')")
    page.get_by_test_id("basemap-select").select_option("osm"); page.get_by_test_id("hillshade-toggle").uncheck()


def test_no_javascript_errors(page):
    assert page.errors == [], page.errors
