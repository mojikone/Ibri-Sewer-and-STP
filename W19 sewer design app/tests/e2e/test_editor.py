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
def bridge(tmp_path_factory):
    """A stand-in VM bridge (jobs, out, done) and a model share holding one SewerGEMS model name: no job reaches the VM."""
    root = tmp_path_factory.mktemp("bridge")
    for d in ("jobs", "out", "done"): (root / d).mkdir()
    (root / "out" / "_alive.txt").write_text("alive")
    share = tmp_path_factory.mktemp("share"); (share / "Area 7").mkdir(); (share / "Area 7" / "Area 7 model.stsw").write_text("not read")
    return dict(root=str(root), share=str(share))


@pytest.fixture(scope="module")
def server(sg_exports, bridge):
    env = dict(os.environ, W19_ASSISTANT_STUB="1", W19_SG_EXPORTS=sg_exports, W19_BRIDGE=bridge["root"],
               W19_MODEL_SHARES=bridge["share"] + "=\\\\VBOXSVR\\TestShare", W19_AGENT_FOLDERS=os.path.join(bridge["root"], "agent_folders.json"))
    p = subprocess.Popen([sys.executable, "-c", "import uvicorn; uvicorn.run('sewerapp.api.app:app', host='127.0.0.1', port=8798)"],
                         cwd=W19, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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
def settings_all(pg):
    """The Settings tab, every group shown (Settings opens on one group since v5)."""
    pg.get_by_test_id("tab-settings").click(); pg.locator("#set-nav button[data-g='*']").click()


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
    settings_all(page)
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
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-design").click()
    expect(page.get_by_test_id("dlg-design")).to_be_visible(); page.get_by_test_id("des-run").click(); idle(page)   # the whole network
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
    settings_all(page)
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
    settings_all(page)
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


def test_profile_route_pick_cursor_sync_zoom_and_export(page, tmp_path):
    nid, lid = draw_network(page)
    page.get_by_test_id("tab-profile").click(); idle(page)
    # a route typed against the flow: from the third manhole back up to the first
    page.get_by_test_id("prof-start").fill(nid[2]); page.get_by_test_id("prof-end").fill(nid[0]); page.get_by_test_id("prof-draw").click(); idle(page)
    page.wait_for_function("prof.rows && prof.rows.length === 2")
    expect(page.locator("#profile-svg .seg")).to_have_count(2)
    assert page.evaluate("prof.rows.every(r => r.reversed)") and "against the flow" in page.get_by_test_id("prof-msg").inner_text()
    assert page.evaluate("prof.segs.length") == 2 and page.evaluate("window.ed.map.getSource('route')._data.features.length") == 4   # 2 lines + S and E
    # manholes drawn as shafts; the pipe that leaves the start manhole off the route (to the outfall) drawn as a circle at its invert
    expect(page.locator("#profile-svg rect.mh")).to_have_count(3)
    j = page.locator("#profile-svg circle.join"); expect(j).to_have_count(1)
    assert lid[2] in j.locator("title").text_content() and "leaves to" in j.locator("title").text_content()
    # picked on the map instead: the first manhole, then the outfall
    page.get_by_test_id("prof-pick").click(); click_at(page, 0, 0); click_at(page, 300, 0); idle(page); page.keyboard.press("Enter")
    page.wait_for_function("prof.rows && prof.rows.length === 3")
    assert page.get_by_test_id("prof-start").input_value() == nid[0] and page.get_by_test_id("prof-end").input_value() == nid[3]
    assert page.evaluate("window.ed.state.routePick") is None
    # the cursor on the profile puts the marker on the map, and the map's cursor on the route moves the profile's
    b = page.locator("#profile-svg").bounding_box()
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 3)
    assert page.evaluate("prof.cursorFrom") == "profile" and page.evaluate("window.ed.map.getSource('cursor')._data.features.length") == 1
    expect(page.get_by_test_id("prof-readout")).to_be_visible()
    xy = page.evaluate("(() => { const p = window.ed.map.project(routePoint(150)), r = window.ed.map.getCanvas().getBoundingClientRect(); return [p.x + r.x, p.y + r.y]; })()")
    page.mouse.move(*xy); page.wait_for_timeout(100)
    assert page.evaluate("prof.cursorFrom") == "map" and abs(page.evaluate("prof.cursor") - 150) < 2
    # zoom along the chainage with the wheel; a double-click shows it all again
    page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 3); page.mouse.wheel(0, -300); page.wait_for_timeout(100)
    r = page.evaluate("prof.range"); assert r and r[1] - r[0] < 300
    page.mouse.dblclick(b["x"] + b["width"] / 2, b["y"] + b["height"] / 3); assert page.evaluate("prof.range") is None
    # the buttons and the scrollbar for long sections
    page.get_by_test_id("prof-zin").click(); r = page.evaluate("prof.range"); assert r and abs((r[1] - r[0]) - 150) < 1
    expect(page.get_by_test_id("prof-scroll")).to_be_visible()
    tb = page.get_by_test_id("prof-thumb").bounding_box(); sb = page.get_by_test_id("prof-scroll").bounding_box()
    page.mouse.move(tb["x"] + tb["width"] / 2, tb["y"] + 5); page.mouse.down(); page.mouse.move(tb["x"] + tb["width"] / 2 + sb["width"] / 4, tb["y"] + 5, steps=5); page.mouse.up()
    r2 = page.evaluate("prof.range"); assert r2[0] > r[0] + 50, (r, r2)
    page.get_by_test_id("prof-zall").click(); assert page.evaluate("prof.range") is None
    expect(page.get_by_test_id("prof-scroll")).to_be_hidden()
    # reverse it, then export
    page.get_by_test_id("prof-swap").click(); idle(page); page.wait_for_function(f"prof.rows && prof.rows[0].from_node === '{nid[3]}'")
    with page.expect_download() as d: page.get_by_test_id("prof-csv").click()
    f = str(tmp_path / "p.csv"); d.value.save_as(f); assert len(open(f).read().strip().splitlines()) == 4
    with page.expect_download() as d: page.get_by_test_id("prof-png").click()
    f = str(tmp_path / "p.png"); d.value.save_as(f); assert open(f, "rb").read(4) == b"\x89PNG"
    page.get_by_test_id("prof-clear").click(); assert page.evaluate("prof.segs.length") == 0


def _screen(pg, x, y):
    """Page pixels of a local-metre point on the map."""
    return pg.evaluate("([lon, lat]) => { const p = window.ed.map.project([lon, lat]), r = window.ed.map.getCanvas().getBoundingClientRect(); return [p.x + r.x, p.y + r.y]; }", ll(x, y))


def test_batch1_cells_paste_trace_box_select_reference_and_reload(page, tmp_path):
    nid, lid = draw_network(page)
    node = lambda i, k: page.evaluate("([i, k]) => window.ed.state.model.nodes.get(i).properties[k]", [i, k])
    link = lambda i, k: page.evaluate("([i, k]) => window.ed.state.model.links.get(i).properties[k]", [i, k])
    # a cell edited in place; Enter moves down a row like a spreadsheet
    page.get_by_test_id("tab-nodes").click()
    cols = page.locator("#tbl-nodes thead th").all_inner_texts()
    page.locator(f'#tbl-nodes tr[data-id="{nid[1]}"] td').nth(cols.index("ground")).dblclick()
    ed_ = page.get_by_test_id("cell-editor"); ed_.fill("101.25"); ed_.press("Enter"); idle(page)
    assert node(nid[1], "ground") == 101.25
    expect(page.get_by_test_id("cell-editor")).to_have_count(1); page.get_by_test_id("cell-editor").press("Escape")
    # a column pasted from a spreadsheet: one edit, the pipe ends follow the inverts, one undo takes it back
    page.locator(f'#tbl-nodes tr[data-id="{nid[0]}"] td').nth(cols.index("invert")).click()
    page.evaluate("t => { const d = new DataTransfer(); d.setData('text/plain', t); document.dispatchEvent(new ClipboardEvent('paste', { clipboardData: d, bubbles: true })); }", "97.9\r\n97.4\r\n96.9\r\n")
    idle(page)
    assert [node(n, "invert") for n in nid[:3]] == [97.9, 97.4, 96.9] and link(lid[0], "up_inv") == 97.9 and link(lid[1], "dn_inv") == 96.9
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert [node(n, "invert") for n in nid[:3]] == [98.0, 97.5, 97.0] and link(lid[0], "up_inv") == 98.0
    # trace: upstream of the third manhole is two pipes; downstream of the first pipe, all three; then its profile
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[2]); page.get_by_test_id("trace-up").click(); idle(page)
    assert sorted(page.evaluate("window.ed.state.sel.ids")) == sorted(lid[:2])
    expect(page.get_by_test_id("trace-box")).to_contain_text("2 pipes")
    page.evaluate("id => window.ed.selectElement('links', id)", lid[0]); page.get_by_test_id("trace-down").click(); idle(page)
    assert sorted(page.evaluate("window.ed.state.sel.ids")) == sorted(lid)
    page.get_by_test_id("trace-profile").click(); idle(page); page.wait_for_function("prof.rows && prof.rows.length === 3")
    # Shift+drag selects the pipes whose middle is in the box (P-1 at 50 m, P-2 at 150 m, not P-3 at 250 m)
    tool(page, "select"); page.get_by_test_id("tab-nodes").click()
    page.get_by_test_id("display-head").click()                         # the Display card folded: it must not lie under the drag
    a, b = _screen(page, 20, -30), _screen(page, 180, 30)
    page.keyboard.down("Shift"); page.mouse.move(*a); page.mouse.down(); page.mouse.move(*b, steps=6); page.mouse.up(); page.keyboard.up("Shift"); idle(page)
    assert page.evaluate("window.ed.state.sel.table") == "links" and sorted(page.evaluate("window.ed.state.sel.ids")) == sorted(lid[:2])
    page.get_by_test_id("display-head").click()
    # a reference layer (a road 20 m off the pipes, no CRS: taken in the project's coordinates), shown and removed
    f = tmp_path / "road.geojson"
    f.write_text('{"type":"FeatureCollection","features":[{"type":"Feature","properties":{"name":"Road 1"},"geometry":{"type":"LineString","coordinates":[[0,20],[300,20]]}}]}')
    page.set_input_files("#ref-file", str(f)); page.wait_for_function("window.ed.state.refs && window.ed.state.refs.length === 1")
    rid = page.evaluate("window.ed.state.refs[0].id")
    assert page.evaluate("id => !!window.ed.map.getLayer('ref-' + id + '-line')", rid)
    c = page.evaluate("window.ed.state.refs[0].geojson.features[0].geometry.coordinates[1]")
    assert abs(c[0] * M_LON - 300) < 0.01 and abs(c[1] * M_LAT - 20) < 0.01
    expect(page.locator("#ref-list .ref")).to_have_count(1)
    # a reload comes back to the same project, with its reference layer
    pid = page.evaluate("window.ed.state.pid"); page.wait_for_timeout(400)
    page.reload(); page.wait_for_function("p => window.ed && window.ed.state.pid === p && window.ed.state.model && document.body.dataset.pending === '0'", arg=pid)
    page.wait_for_function("window.ed.state.refs && window.ed.state.refs.length === 1")
    assert page.evaluate("window.ed.counts()") == {"nodes": 4, "links": 3}
    page.locator('#ref-list .ref [data-act="del"]').click(); idle(page)
    assert page.evaluate("window.ed.state.refs.length") == 0 and not page.evaluate("id => !!window.ed.map.getLayer('ref-' + id + '-line')", rid)


def test_batch2_scenarios_summary_design_quantities(page, tmp_path):
    nid, lid = draw_network(page)
    sel_link = lambda l: page.evaluate("id => window.ed.selectElement('links', id)", l)
    # a copy, renamed in the scenario manager, with a bigger pipe; compared with the base
    page.get_by_test_id("copy-btn").click(); idle(page)
    page.get_by_test_id("scen-btn").click(); expect(page.locator("#scen-list .scrow")).to_have_count(2)
    page.locator("#scen-list .scrow.cur [data-a=rename]").click(); page.get_by_test_id("ask-input").fill("bigger"); page.get_by_test_id("ask-ok").click(); idle(page)
    expect(page.locator("#scen-list .scrow.cur .scname")).to_contain_text("bigger")
    page.get_by_test_id("scen-close").click()
    sel_link(lid[1]); page.get_by_test_id("prop-dn_mm").select_option("315"); idle(page)
    page.get_by_test_id("scen-btn").click(); page.locator("#scen-list .scrow:not(.cur) [data-a=compare]").click(); idle(page)
    assert page.evaluate("window.ed.state.colorBy") == "compare" and page.evaluate(f"window.ed.state.compare.change['{lid[1]}']") == "size"
    expect(page.get_by_test_id("legend")).to_contain_text("size changed (1)")
    assert lid[1] in page.locator("#tbl-toolout").inner_text()
    # the summary: tiles and bar charts; a bar selects its pipes
    page.get_by_test_id("tab-summary").click(); idle(page)
    expect(page.locator("#ch-dn .bar")).to_have_count(2)                       # DN200 and DN315
    page.locator("#ch-dn .bar").last.click(); assert page.evaluate("window.ed.state.sel.ids") == [lid[1]]
    # design: a locked pipe keeps its size; the preview changes nothing until applied
    sel_link(lid[0]); page.get_by_test_id("lock-on").click(); idle(page)
    expect(page.get_by_test_id("lock-state")).to_have_text("locked")
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
    ld = page.get_by_test_id("load-design"); ld.fill("5000"); ld.press("Enter"); idle(page)
    before = page.evaluate("Object.fromEntries([...window.ed.state.model.links.values()].map(f => [f.id, f.properties.dn_mm]))")
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-design").click(); page.get_by_test_id("des-preview").click(); idle(page)
    expect(page.get_by_test_id("toolout-apply")).to_be_visible()
    assert page.evaluate("Object.fromEntries([...window.ed.state.model.links.values()].map(f => [f.id, f.properties.dn_mm]))") == before
    page.get_by_test_id("toolout-apply").click(); idle(page)
    after = page.evaluate("Object.fromEntries([...window.ed.state.model.links.values()].map(f => [f.id, f.properties.dn_mm]))")
    assert after[lid[0]] == 200 and after[lid[2]] > 200, after
    # quantities in the BOQ structure, and their CSV
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-quantities").click(); idle(page)
    assert "Pipe DN" in page.locator("#tbl-toolout").inner_text() and "Manhole Type" in page.locator("#tbl-toolout").inner_text()
    with page.expect_download() as d: page.get_by_test_id("toolout-csv").click()
    f = str(tmp_path / "q.csv"); d.value.save_as(f); assert open(f).readline().startswith("item,band,unit,qty")
    # the copy deleted from the manager: back on the base
    page.get_by_test_id("scen-btn").click(); page.locator("#scen-list .scrow.cur [data-a=del]").click(); page.get_by_test_id("ask-ok").click(); idle(page)
    assert page.evaluate("window.ed.state.sid") == "base" and page.get_by_test_id("scenario-select").locator("option").count() == 1
    page.get_by_test_id("scen-close").click()


def test_batch2_storm_slider_saved_route_and_assistant_on_the_map(page):
    pid = page.evaluate("window.ed.state.pid")
    page.set_input_files("#import-file", EXTRAN1)
    page.wait_for_function("p => window.ed.state.pid !== p && window.ed.state.model && document.body.dataset.pending === '0'", arg=pid)
    page.get_by_test_id("tools-btn").click(); page.get_by_test_id("tool-run-storm").click(); idle(page)
    expect(page.get_by_test_id("storm-bar")).to_be_visible()
    page.get_by_test_id("storm-t").fill("20"); idle(page); page.wait_for_function("window.ed.state.stormFrame && window.ed.state.stormFrame.period === 20")
    assert page.get_by_test_id("storm-time").inner_text().startswith("t = ")
    page.get_by_test_id("storm-peak").click(); assert page.evaluate("window.ed.state.stormFrame") is None
    # the profile carries the storm's peak level; the route is saved with the project
    first = page.evaluate("window.ed.state.model.linkFeat[0].properties.from_node")
    page.get_by_test_id("tab-profile").click(); page.get_by_test_id("prof-start").fill(first); page.get_by_test_id("prof-draw").click(); idle(page)
    page.wait_for_function("prof.rows && prof.rows.length > 0"); expect(page.locator("#profile-svg polyline.storm")).to_have_count(1)
    page.get_by_test_id("prof-save-route").click(); page.get_by_test_id("ask-input").fill("main"); page.get_by_test_id("ask-ok").click(); idle(page)
    assert page.evaluate("window.ed.state.routes.map(r => r.name)") == ["main"]
    # the assistant gets the selection and the route, and its map actions are applied (reply mocked)
    ids = page.evaluate("window.ed.state.model.linkFeat.slice(0, 2).map(f => String(f.id))")
    page.get_by_test_id("tab-assistant").click()                    # (on the Profile tab a selection would redraw the profile from it)
    page.evaluate("id => window.ed.selectElement('links', id)", ids[0])
    sent = {}
    def fake(route):
        import json as _j
        sent.update(_j.loads(route.request.post_data))
        route.fulfill(status=200, content_type="application/json", body=_j.dumps(dict(reply="Here they are.", tool_calls=[], usage={},
                      ui_actions=[dict(kind="select", table="links", ids=ids)])))
    page.route("**/api/g/assistant", fake)
    page.get_by_test_id("tab-assistant").click(); page.get_by_test_id("asst-input").fill("Show me these"); page.get_by_test_id("asst-input").press("Enter")
    expect(page.get_by_test_id("asst-action")).to_contain_text("shown on the map: 2 links"); idle(page)
    page.unroute("**/api/g/assistant")
    assert sent["selection"] == {"table": "links", "ids": [ids[0]]} and sent["route"]["start"] == first
    assert sorted(page.evaluate("window.ed.state.sel.ids")) == sorted(ids)


def test_any_sewergems_model_exported_through_the_bridge_then_opened(page, bridge, sg_exports):
    import shutil, glob
    os.utime(os.path.join(bridge["root"], "out", "_alive.txt"))                       # the watcher's heartbeat
    file_menu(page, "sg-btn")
    expect(page.get_by_test_id("sg-watch")).to_contain_text("bridge is running")
    row = page.locator("#sg-models .sgm", has_text="Area 7 model.stsw"); expect(row).to_have_count(1)
    row.locator("button[data-act=export]").click(); idle(page)
    jobs = glob.glob(os.path.join(bridge["root"], "jobs", "w19x_*_Area_7_model.ps1")); assert len(jobs) == 1
    body = open(jobs[0], encoding="utf-8").read()
    assert "$src = '\\\\VBOXSVR\\TestShare\\Area 7\\Area 7 model.stsw'" in body and "$tag = 'Area_7_model'" in body
    assert "Copy-Item -LiteralPath $src" in body and "SaveAs($work)" in body                  # a copy is opened, never the model
    expect(page.locator("#sg-jobs .sgj")).to_contain_text("waiting for the VM")
    # the VM's part, played here: the watcher runs the job, SewerGEMS writes the export, scenarios.csv last
    name = os.path.basename(jobs[0])[:-4]
    open(os.path.join(bridge["root"], "out", name + ".txt"), "w").write("ok\n__EXIT__ 0\n")
    shutil.move(jobs[0], os.path.join(bridge["root"], "done"))
    shutil.copytree(os.path.join(sg_exports, "SC1-2056_final"), os.path.join(sg_exports, "Area_7_model"))
    open(os.path.join(sg_exports, "Area_7_model", "log.txt"), "w").write("  scenario 1 'design' -> s001\n  scenario 2 'check' -> s002\n")
    page.wait_for_function("document.querySelector('#sg-jobs .sgj.ready')", timeout=15000)
    page.locator("#sg-jobs .sgj.ready button[data-act=open]").click()
    page.wait_for_function("window.ed.state.info && window.ed.state.info.name.includes('Area_7_model') && window.ed.state.model && document.body.dataset.pending === '0'", timeout=240000)
    assert page.get_by_test_id("scenario-select").locator("option").count() == 2


def test_failing_pipes_can_be_hidden_and_stay_off_other_colourings(page):
    nid, lid = draw_network(page)
    page.evaluate("id => window.ed.selectElement('nodes', id)", nid[0])
    ld = page.get_by_test_id("load-design"); ld.fill("5000"); ld.press("Enter"); idle(page)
    assert summary(page)["over_limit"] > 0
    vis = lambda: page.evaluate("window.ed.map.getLayoutProperty('links-fail', 'visibility')")
    assert vis() == "visible" and page.evaluate("window.ed.state.model.linkFeat.some(f => f.properties._fail === 1)")
    page.get_by_test_id("fail-toggle").uncheck(); assert vis() == "none"
    expect(page.get_by_test_id("legend-fail")).to_contain_text("hidden")
    page.get_by_test_id("legend-fail").click(); assert vis() == "visible" and page.get_by_test_id("fail-toggle").is_checked()
    page.get_by_test_id("color-by").select_option("storm_cap"); idle(page)               # another colouring: no red overlay
    assert not page.evaluate("window.ed.state.model.linkFeat.some(f => f.properties._fail === 1)")
    expect(page.get_by_test_id("legend-fail")).to_have_count(0)
    page.get_by_test_id("color-by").select_option("v_ms"); idle(page)


def test_settings_tables_edited_applied_and_undone(page):
    draw_network(page)
    settings_all(page); idle(page)
    fs = page.locator("#tbl-design-slope_min")
    first = fs.locator('input[data-c="0"]').first; assert first.input_value() == "200"
    g = fs.locator('input[data-c="1"]').first; assert float(g.input_value()) == 0.5             # G203 Table 11: 5 mm/m for DN200
    g.fill("0.6"); page.get_by_test_id("apply-design-slope_min").click(); idle(page)
    assert page.evaluate("window.ed.state.model.settings.design.slope_min['200']") == pytest.approx(0.006)
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert page.evaluate("window.ed.state.model.settings.design.slope_min['200']") == pytest.approx(0.005)
    # a size added to the catalogue becomes a choice in the property grid
    cat = page.locator("#tbl-design-catalogue"); cat.locator("[data-act=add]").click()
    cat = page.locator("#tbl-design-catalogue"); cat.locator('input[data-c="0"]').last.fill("2200"); cat.locator('input[data-c="1"]').last.fill("1941")
    page.get_by_test_id("apply-design-catalogue").click(); idle(page)
    assert 2200 in page.evaluate("window.ed.state.info.catalogue")
    assert page.evaluate("window.ed.state.rain.idf.length") == 0                                    # the rain rows were not touched


def test_a_pipe_becomes_a_box_with_barrels_then_a_circle_again(page):
    nid, lid = draw_network(page)
    page.evaluate("id => window.ed.selectElement('links', id)", lid[1]); idle(page)
    sh = page.get_by_test_id("sec-shape"); assert sh.input_value() == "circle"
    sh.select_option("box")
    page.get_by_test_id("sec-span_m").fill("2"); page.get_by_test_id("sec-rise_m").fill("1"); page.get_by_test_id("sec-barrels").fill("2")
    page.get_by_test_id("sec-apply").click(); idle(page)
    p = page.evaluate("id => window.ed.state.model.linkFeat.find(f => f.id === id).properties", lid[1])
    assert p["section"] == "2 x Box 2 x 1 m" and p["sec"]["barrels"] == 2 and p["dn_mm"] == 0
    assert result(page, lid[1], "depth_m") > 0 and result(page, lid[1], "q_full_ls") > 0 and summary(page)["not_analysed"] == 0
    expect(page.get_by_test_id("res-depth_m")).to_be_visible(); expect(page.get_by_test_id("res-yc_m")).to_be_visible()
    assert page.get_by_test_id("sec-shape").input_value() == "box" and page.get_by_test_id("sec-barrels").input_value() == "2"
    page.get_by_test_id("sec-barrels").fill("1.5"); page.get_by_test_id("sec-apply").click(); idle(page)   # refused in the page
    assert page.evaluate("id => window.ed.state.model.linkFeat.find(f => f.id === id).properties.sec.barrels", lid[1]) == 2
    page.get_by_test_id("sec-shape").select_option("circle"); page.get_by_test_id("sec-apply").click(); idle(page)
    p = page.evaluate("id => window.ed.state.model.linkFeat.find(f => f.id === id).properties", lid[1])
    assert "sec" not in p and p["dn_mm"] > 0 and result(page, lid[1], "d_over_D") > 0
    page.get_by_test_id("undo-btn").click(); idle(page)
    assert page.evaluate("id => window.ed.state.model.linkFeat.find(f => f.id === id).properties.sec.shape", lid[1]) == "box"


def test_symbology_colour_by_any_field_labels_and_named_definitions(page):
    nid, lid = draw_network(page)
    feat = lambda t, i: page.evaluate("([t, i]) => window.ed.state.model[t].find(f => f.id === i).properties", [t, i])
    assert feat("linkFeat", lid[0])["_lab"].startswith("DN")                       # the Default labels: as before
    page.get_by_test_id("sym-edit").click(); expect(page.get_by_test_id("dlg-sym")).to_be_visible()
    page.get_by_test_id("sym-new").click()
    page.get_by_test_id("sym-field").select_option("up_inv")                         # pipes by upstream invert, 3 classes
    page.get_by_test_id("sym-steps").fill("3"); page.get_by_test_id("sym-init").click()
    assert page.locator("#sym-coding-ed tbody tr").count() == 4                       # 3 classes and the one above
    page.get_by_test_id("sym-apply").click(); idle(page)
    cb = page.evaluate("window.ed.state.colorBy"); assert cb.startswith("sym:")
    assert page.get_by_test_id("color-by").input_value() == cb
    cols = {feat("linkFeat", i)["_c"] for i in lid}; assert len(cols) >= 2, cols        # the pipes differ in invert
    rows = page.locator("#legend .sym-row"); assert rows.count() == 4
    first = rows.first; first.click(); idle(page)                                      # a legend row selects its pipes
    assert page.evaluate("window.ed.state.sel.table") == "links" and len(page.evaluate("window.ed.state.sel.ids")) >= 1
    # size instead of colour: line widths follow the classes
    page.get_by_test_id("sym-mode").select_option("size"); page.get_by_test_id("sym-apply").click(); idle(page)
    assert all("_w" in feat("linkFeat", i) for i in lid)
    # labels: a free-text label with a field, its decimals and unit
    page.get_by_test_id("sym-lab-free").click()
    page.locator("#sym-labels tbody tr").last.locator("[data-k=template]").fill("L={length_m:1:u}")
    page.get_by_test_id("sym-lab-apply").click(); idle(page)
    assert "L=100.0 m" in feat("linkFeat", lid[0])["_lab"]
    # structures by depth: their own select appears on the Display card
    page.locator("#sym-tabs button[data-type=nodes]").click(); page.get_by_test_id("sym-new").click()
    page.get_by_test_id("sym-apply").click(); idle(page)
    expect(page.get_by_test_id("node-color-by")).to_be_visible()
    assert all("_c" in feat("nodeFeat", i) for i in nid)
    page.get_by_test_id("sym-close").click()
    # a second named symbology starts as a copy; switching back restores the first
    page.get_by_test_id("sym-edit").click(); page.get_by_test_id("sym-def-new").click()
    page.get_by_test_id("ask-input").fill("Review"); page.get_by_test_id("ask-ok").click(); idle(page)
    assert page.get_by_test_id("sym-def").input_value() == "Review"
    page.get_by_test_id("sym-close").click()
    page.get_by_test_id("sym-def").select_option("Default"); idle(page)
    # kept with the project: the server has both definitions
    pid = page.evaluate("window.ed.state.pid")
    s = page.evaluate("pid => fetch(`/api/g/projects/${pid}/symbology`).then(r => r.json())", pid)
    assert set(s["defs"]) == {"Default", "Review"} and s["active"] == "Default"
    # back to a built-in colouring: the custom coding stops painting the pipes
    page.get_by_test_id("color-by").select_option("v_ms"); idle(page)
    assert "_w" not in feat("linkFeat", lid[0]) and page.locator("#legend .sym-row[data-type=links]").count() == 0


def test_no_javascript_errors(page):
    assert page.errors == [], page.errors


# ------------------------------------------------------------------ v2 (2026-11-23): the ribbon, layout runs, morph, reconnect, units
def vtool(pg, name):
    """In the ribbon the old tool strip is hidden: press its button as the ribbon does."""
    pg.evaluate("n => document.getElementById('tool-' + n).click()", name)


def test_v2_ribbon_layout_run_morph_reconnect_units_and_pond(server, browser):
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    assert not pg.locator("#topbar").is_visible() and pg.locator("#ribbon").is_visible()
    # File > New (a local-metre project)
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-new").click(); pg.get_by_test_id("new-name").fill("Ribbon")
    pg.get_by_test_id("new-crs-mode").select_option("local"); pg.get_by_test_id("new-create").click()
    pg.wait_for_function("window.ed.state.pid && window.ed.state.model && document.body.dataset.pending === '0'")
    # Layout: a 230 m run at a 100 m maximum gives 80 + 80 + 70 (the engineer's rule), one undo step
    pg.click("#rb-tab-layout"); pg.locator("#rb-page-layout .rb-btn", has_text="Layout").first.click()
    pg.select_option("#layout-spacing", "custom"); pg.fill("#layout-custom", "100"); pg.dispatch_event("#layout-custom", "change")
    click_at(pg, 0, 0); idle(pg); click_at(pg, 230, 0); idle(pg)
    lens = sorted(round(x, 3) for x in pg.evaluate("window.ed.state.model.linkFeat.map(f => f.properties.length_m)"))
    assert lens == [70.0, 80.0, 80.0], lens
    click_at(pg, 230, -60); idle(pg)                                         # the run goes on from the last structure
    assert len(ids(pg, "links")) == 4
    pg.keyboard.press("Escape")
    pg.get_by_test_id("qat-undo-btn").click(); idle(pg); assert len(ids(pg, "links")) == 3
    # morph: the outfall tool on the run's last structure turns it into an outfall (keeping its pipes)
    last = pg.evaluate("window.ed.state.model.links.get(window.ed.state.model.linkFeat.find(f => !window.ed.state.model.linkFeat.some(g => g.properties.from_node === f.properties.to_node)).id).properties.to_node")
    vtool(pg, "outfall"); click_at(pg, 230, 0); idle(pg)
    assert pg.evaluate("id => window.ed.state.model.nodes.get(id).properties.kind", last) == "outfall" and len(ids(pg, "links")) == 3
    # right-click a pipe: Reverse; then Reconnect its stop to a new manhole
    vtool(pg, "select")
    pg.evaluate("window.ed.ctx(40 / 111319.49, 0)"); expect(pg.locator("#ctx-menu")).to_be_visible()
    first = pg.evaluate("window.ed.state.sel.ids[0]")
    pg.get_by_test_id("ctx-reverse").click(); idle(pg)
    p = pg.evaluate("id => window.ed.state.model.links.get(id).properties", first)
    vtool(pg, "manhole"); click_at(pg, 40, 60); idle(pg); vtool(pg, "select")
    new = [n for n in ids(pg, "nodes") if pg.evaluate("id => window.ed.state.model.nodes.get(id).geometry.coordinates[1]", n) > 0][0]
    pg.evaluate("window.ed.ctx(40 / 111319.49, 0)"); pg.get_by_test_id("ctx-reconnect-to").click()
    click_at(pg, 40, 60); idle(pg)
    assert pg.evaluate("id => window.ed.state.model.links.get(id).properties.to_node", first) == new
    assert p["from_node"] != pg.evaluate("id => window.ed.state.model.links.get(id).properties.to_node", first)
    # box select (Home > Box): a drag over the whole run selects its pipes; the navigator finds the connected network
    pg.click("#rb-tab-home"); pg.locator("#rb-page-home [data-testid=rb-box]").click()
    r = pg.evaluate("(() => { const b = window.ed.map.getCanvas().getBoundingClientRect(); const a = window.ed.map.project([-20 / 111319.49, 80 / 110574]), c = window.ed.map.project([260 / 111319.49, -20 / 110574]); return [b.left + a.x, b.top + a.y, b.left + c.x, b.top + c.y]; })()")
    pg.mouse.move(r[0], r[1]); pg.mouse.down(); pg.mouse.move((r[0] + r[2]) / 2, (r[1] + r[3]) / 2, steps=4); pg.mouse.move(r[2], r[3], steps=4); pg.mouse.up(); idle(pg)
    assert pg.evaluate("window.ed.state.sel.table") == "links" and len(pg.evaluate("window.ed.state.sel.ids")) == 3
    pg.evaluate("id => window.ed.selectElement('nodes', id)", new)
    pg.locator("#rb-page-home [data-testid=rb-connected]").click(); idle(pg)
    assert sorted(pg.evaluate("window.ed.state.sel.ids")) == sorted(ids(pg, "links"))
    pg.locator("#rb-page-home [data-testid=rb-find-]").click(); pg.get_by_test_id("ctx-find-isolated").click()
    pg.keyboard.press("Escape"); pg.evaluate("document.getElementById('tool-select').click()")    # units: loads typed in L/s are stored in m3/d
    pg.click("#rb-tab-components"); pg.locator("#rb-page-components .rb-btn", has_text="Units").click()
    pg.get_by_test_id("units-flow_load").select_option("L/s"); pg.locator("#dlg-units [data-act=ok]").click()
    n0 = ids(pg, "nodes")[0]; pg.evaluate("id => window.ed.selectElement('nodes', id)", n0)
    ld = pg.get_by_test_id("load-design"); ld.fill("1"); ld.press("Enter"); idle(pg)
    assert abs(pg.evaluate("id => window.ed.state.model.loads.design[id]", n0) - 86.4) < 1e-6
    # collapse the ribbon (double-click a tab), and back
    pg.dblclick("#rb-tab-view"); assert not pg.locator("#rb-panel").is_visible()
    pg.dblclick("#rb-tab-view"); assert pg.locator("#rb-panel").is_visible()
    # the pond sample: rain fills it, the pump starts at its depth
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-sample").click(); pg.locator("#sample-list button", has_text="Pond").click(); idle(pg)
    pg.click("#rb-tab-home"); pg.locator("#rb-page-home .rb-btn", has_text="Run storm").click(); idle(pg)
    assert abs(pg.evaluate("window.ed.state.storm.data.links['PMP-1'].q_peak") - 0.12) < 0.002
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v2_ribbon.png")); ctx.close()


def test_v3_pump_station_force_main_unit_loads_notifications_query(server, browser):
    """A wet well, a pump and a force main drawn with the tools; the pump defined in Pump definitions; its status in
    Properties; unit loads; Validate; a query; the table's statistics row (2026-11-23 v3)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-new").click(); pg.get_by_test_id("new-name").fill("Station")
    pg.get_by_test_id("new-crs-mode").select_option("local"); pg.get_by_test_id("new-create").click()
    pg.wait_for_function("window.ed.state.pid && window.ed.state.model && document.body.dataset.pending === '0'")
    vtool(pg, "manhole"); click_at(pg, 0, 0); vtool(pg, "wetwell"); click_at(pg, 60, 0); vtool(pg, "pjunction"); click_at(pg, 70, 20)
    vtool(pg, "outfall"); click_at(pg, 300, 40); idle(pg)
    vtool(pg, "pipe"); click_at(pg, 0, 0); click_at(pg, 60, 0); vtool(pg, "pump"); click_at(pg, 60, 0); click_at(pg, 70, 20)
    vtool(pg, "ppipe"); click_at(pg, 70, 20); click_at(pg, 300, 40); idle(pg)
    kinds = pg.evaluate("Object.fromEntries(window.ed.state.model.linkFeat.map(f => [f.id, f.properties.kind]))")
    assert sorted(kinds.values()) == ["conduit", "pressure_pipe", "pump"], kinds
    pump = [k for k, v in kinds.items() if v == "pump"][0]
    nodes = {f: pg.evaluate("i => window.ed.state.model.nodes.get(i).properties.kind", f) for f in ids(pg, "nodes")}
    vtool(pg, "select")
    for n, k in nodes.items():                                                   # levels: wet well low, outfall high
        g, i = {"manhole": (104, 102), "wetwell": (104, 99), "pressure_junction": (104, 102), "outfall": (118, 116)}[k]
        pg.evaluate("id => window.ed.selectElement('nodes', id)", n); set_prop(pg, "ground", g); set_prop(pg, "invert", i)
    mh = [n for n, k in nodes.items() if k == "manhole"][0]
    pg.evaluate("id => window.ed.selectElement('nodes', id)", mh); ld = pg.get_by_test_id("load-design"); ld.fill("864"); ld.press("Enter"); idle(pg)   # 10 L/s, about 27 L/s once peaked
    # Components > Pump definitions: a design point of 30 L/s at 25 m, then the pump takes it
    pg.evaluate("id => window.ed.selectElement('links', id)", pump)
    pg.click("#rb-tab-components"); pg.locator("#rb-page-components .rb-btn", has_text="Pump definitions").click()
    pg.get_by_test_id("pd-add").click(); pg.fill("[data-testid=pd-q_ls]", "30"); pg.fill("[data-testid=pd-h_m]", "25")
    pg.locator("#dlg-pumps [data-act=ok]").click(); idle(pg); pg.locator("#dlg-pumps [data-act=close]").click()
    pg.get_by_test_id("pu-def").select_option("Pump 1"); pg.fill("#pu-on", "1.5"); pg.fill("#pu-off", "0.5"); pg.get_by_test_id("pu-apply").click(); idle(pg)
    st = pg.get_by_test_id("pump-status").inner_text()
    assert "delivers the flow" in st, st                                      # about 27 L/s against about 19 m: a 30 L/s @ 25 m pump copes
    assert pg.evaluate(f"window.ed.state.results.links['{pump}'].tdh_m") > 116.2 - 100.5 - 0.01       # at least the static lift
    # unit loads: 500 people on the manhole raise the flow
    pg.get_by_test_id("rb-unit-loads-").click(); pg.get_by_test_id("ul-add").click(); pg.locator("#dlg-units-lib [data-act=ok]").click(); idle(pg)
    q0 = pg.evaluate(f"window.ed.state.results.links['{pump}'].q_ls")
    pg.evaluate("id => window.ed.selectElement('nodes', id)", mh); pg.get_by_test_id("ur-add").click(); pg.locator(".ur [data-k=c]").last.fill("500")
    pg.get_by_test_id("ur-apply").click(); idle(pg)
    assert pg.evaluate(f"window.ed.state.results.links['{pump}'].q_ls") > q0
    # Validate lists the network's notes; a query selects the conduits
    pg.click("#rb-tab-analysis"); pg.locator("#rb-page-analysis .rb-btn", has_text="Validate").first.click(); idle(pg)
    expect(pg.locator("#pane-notes")).to_be_visible()
    pg.click("#rb-tab-home"); pg.locator("#rb-page-home .rb-btn", has_text="Query").click()
    pg.select_option("#q-f", "kind"); pg.select_option("#q-o", "="); pg.fill("#q-v", "pressure_pipe"); pg.locator("#dlg-query [data-act=ok]").click()
    assert pg.evaluate("window.ed.state.sel.ids").__len__() == 1; pg.locator("#dlg-query [data-act=close]").click()
    pg.evaluate("document.getElementById('tab-links').click()"); expect(pg.locator("#tbl-links tfoot")).to_have_count(1)
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v3_station.png")); ctx.close()


def test_v4_gvf_profile_controls_rational_batch_and_option_sets(server, browser):
    """GVF chosen in Settings draws its water levels; the pond sample gets a control rule, curve-number infiltration and
    a run; a drawn catchment gets C and Tc for the rational method; a batch run; a named set of options (2026-11-23 v4)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-sample").click(); pg.locator("#sample-list button", has_text="Pond").click(); idle(pg)
    # Components > Controls: the pump starts above 1.2 m in the wet well
    pg.click("#rb-tab-components"); pg.locator("#rb-page-components .rb-btn", has_text="Controls").click(); pg.get_by_test_id("ctl-add").click()
    pg.locator("#dlg-ctl tr[data-i] [data-f=value]").fill("1.2"); pg.locator("#dlg-ctl [data-act=ok]").click(); idle(pg)
    assert pg.evaluate("window.ed.state.model.controls.length") == 1
    # the catchment: C, Tc and a curve number
    pg.evaluate("window.ed.selectElement('catchments', 'CM-1')"); pg.wait_for_timeout(200)
    pg.fill("#hy-C", "0.85"); pg.fill("#hy-tc", "12"); pg.fill("#hy-cn", "88"); pg.get_by_test_id("hy-apply").click(); idle(pg)
    # Settings: curve-number infiltration and the GVF profile
    pg.evaluate("document.getElementById('tab-settings').click()"); pg.wait_for_timeout(300); pg.locator("#set-nav button[data-g='*']").click()
    pg.select_option("[data-testid='set-storm_infiltration']", "curve_number"); idle(pg)
    pg.select_option("[data-testid='set-flow_profile']", "gvf"); idle(pg)
    pg.click("#rb-tab-home"); pg.locator("#rb-page-home .rb-btn", has_text="Run storm").click(); idle(pg)
    assert pg.evaluate("window.ed.state.storm.data.links['PMP-1'].q_peak") > 0
    # the rational method on the pond's inlet pipe
    pg.click("#rb-tab-analysis"); pg.locator("#rb-page-analysis .rb-btn", has_text="Rational method").click(); idle(pg)
    expect(pg.locator("#tbl-toolout")).to_contain_text("POS-1")
    # batch run and a named set of options
    pg.evaluate("document.getElementById('copy-btn').click()"); idle(pg)
    pg.locator("#rb-page-analysis .rb-btn", has_text="Batch run").click(); pg.locator("#dlg-batch [data-act=ok]").click(); idle(pg)
    assert pg.locator("#tbl-toolout tbody tr").count() == 2
    pg.locator("#rb-page-analysis .rb-btn", has_text="Calculation options").click(); pg.get_by_test_id("ctx-co-save").click()
    pg.get_by_test_id("ask-input").fill("GVF storm"); pg.get_by_test_id("ask-ok").click(); idle(pg)
    assert "GVF storm" in pg.evaluate("Object.keys(window.ed.state.model.settings.calc_option_sets)")
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v4.png")); ctx.close()


def test_v5_mixed_selection_settings_alternatives_and_agent_folders(server, browser, tmp_path):
    """Pipes and structures selected together and deleted in one step; Settings by group; a loading alternative shared
    by two scenarios; the assistant's folders and a stand-in answer (2026-11-23 v5, F13-F21)."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-new").click(); pg.get_by_test_id("new-name").fill("Mixed")
    pg.get_by_test_id("new-crs-mode").select_option("local"); pg.get_by_test_id("new-create").click()
    pg.wait_for_function("window.ed.state.pid && window.ed.state.model && document.body.dataset.pending === '0'")
    pg.click("#rb-tab-layout"); pg.locator("#rb-page-layout .rb-btn", has_text="Layout").first.click()
    pg.select_option("#layout-spacing", "custom"); pg.fill("#layout-custom", "100"); pg.dispatch_event("#layout-custom", "change")
    click_at(pg, 0, 0); idle(pg); click_at(pg, 230, 0); idle(pg); pg.keyboard.press("Escape"); vtool(pg, "select")
    L, N = ids(pg, "links"), ids(pg, "nodes")
    # F13: a pipe, then Ctrl+click a structure: both selected, the bar names them, Delete removes both in one step
    pg.evaluate("([l, n]) => { selClick('links', l, false); selClick('nodes', n, true); }", [L[0], N[-1]])
    expect(pg.get_by_test_id("mix-bar")).to_contain_text("1 pipe"); expect(pg.get_by_test_id("mix-bar")).to_contain_text("1 structure")
    pg.evaluate("document.activeElement && document.activeElement.blur()"); pg.keyboard.press("Delete"); idle(pg)
    assert L[0] not in ids(pg, "links") and N[-1] not in ids(pg, "nodes")
    pg.get_by_test_id("qat-undo-btn").click(); idle(pg)
    assert sorted(ids(pg, "links")) == sorted(L) and sorted(ids(pg, "nodes")) == sorted(N)
    # F19/F20: Settings by group, Design constraints on its own
    pg.evaluate("document.getElementById('tab-settings').click()"); pg.wait_for_timeout(300)
    pg.locator("#set-nav button[data-g='Design constraints']").click()
    vis = pg.evaluate("[...document.querySelectorAll('#settings-form > fieldset')].filter(f => !f.hidden).map(f => f.querySelector('legend').textContent.trim())")
    assert "Design limits" in vis and "Friction" not in vis, vis
    # F14: a loading alternative made in the base and taken by a copy: a load set in one shows in the other
    pg.click("#rb-tab-home"); pg.locator("#rb-page-home .rb-btn", has_text="Alternatives").click()
    pg.get_by_test_id("alt-new-loading").click(); pg.get_by_test_id("ask-input").fill("Loads 2051"); pg.get_by_test_id("ask-ok").click(); idle(pg)
    expect(pg.get_by_test_id("alt-use-loading")).to_have_value("A1")
    pg.locator("#dlg-alts [data-act=close]").click()
    n0 = N[0]; pg.evaluate("id => window.ed.selectElement('nodes', id)", n0)
    ld = pg.get_by_test_id("load-design"); ld.fill("100"); ld.press("Enter"); idle(pg)
    pg.evaluate("document.getElementById('copy-btn').click()"); idle(pg)
    sid = pg.evaluate("window.ed.state.sid"); assert sid != "base"
    assert abs(pg.evaluate("id => window.ed.state.model.loads.design[id]", n0) - 100) < 1e-6         # the copy takes A1 too
    alts = pg.evaluate("fetch('/api/g/projects/' + window.ed.state.pid + '/alternatives').then(r => r.json())")
    assert alts["alternatives"]["loading"][0]["edits"] == 1 and set(alts["alternatives"]["loading"][0]["used_by"]) == {"base", sid}
    # F21: the assistant's folders, then a stand-in answer
    (tmp_path / "gis").mkdir()
    pg.evaluate("document.getElementById('tab-assistant').click()"); pg.click("#asst-folders")
    pg.get_by_test_id("folder-path").fill(str(tmp_path / "gis")); pg.locator("#dlg-folders [data-act=ok]").click()
    expect(pg.get_by_test_id("folder-list")).to_contain_text("gis"); pg.locator("#dlg-folders [data-act=close]").click()
    pg.fill("#asst-input", "How many pipes?"); pg.click("#asst-send")
    expect(pg.get_by_test_id("asst-reply")).to_contain_text("Stub answer")
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v5.png")); ctx.close()


def test_v5_phone_layout_keeps_the_map_and_opens_properties_as_a_drawer(server, browser):
    """On a phone the map keeps the screen: Properties opens over it when an element is chosen, and closes again."""
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/sample/pond', {method: 'POST'}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    pg.wait_for_function("document.body.classList.contains('compact-ui')")
    mw = pg.evaluate("document.getElementById('map-wrap').getBoundingClientRect().width")
    assert mw > 360, mw                                                     # the map has the width
    assert not pg.locator("#props").is_visible()
    pg.evaluate("window.ed.selectElement('nodes', 'WW-1')"); pg.wait_for_timeout(200)
    expect(pg.locator("#props")).to_be_visible()
    pw = pg.evaluate("document.getElementById('props').getBoundingClientRect()")
    assert pw["width"] <= 360 and pw["right"] <= 376                        # a drawer inside the screen
    pg.evaluate("setSel(null, [])"); pg.wait_for_timeout(200)
    assert not pg.locator("#props").is_visible()
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v5_phone.png")); ctx.close()
    

def test_v5_phone_drawing_a_manhole_leaves_properties_closed(server, browser):
    """The engineer, 2026-11-23: on a phone, Properties opened on every manhole drawn. Now only Select opens it, and a
    drawing tool folds it away."""
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/sample/pond', {method: 'POST'}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    pg.wait_for_function("document.body.classList.contains('compact-ui')")
    pg.evaluate("window.ed.selectElement('nodes', 'WW-1')"); pg.wait_for_timeout(200)
    expect(pg.locator("#props")).to_be_visible()                                  # Select still opens it
    pg.evaluate("setTool('manhole')"); pg.wait_for_timeout(200)
    assert not pg.locator("#props").is_visible()                                   # a drawing tool: the map
    n0 = pg.evaluate("state.model.nodes.size")
    b = pg.evaluate("(() => { const r = document.getElementById('map').getBoundingClientRect(); return [r.left + r.width / 2, r.top + r.height / 3]; })()")
    pg.mouse.click(b[0], b[1]); idle(pg); pg.wait_for_function(f"state.model.nodes.size > {n0}")
    pg.wait_for_timeout(300)
    assert not pg.locator("#props").is_visible()                                   # the new manhole is chosen, Properties stays shut
    assert errs == [], errs
    ctx.close()


def test_v5_phone_bottom_pane_opens_with_a_tap_and_resizes_with_a_finger(server, browser):
    """A real touch (Chrome DevTools touch events): a tap on the splitter opens the tables, a drag resizes them, and the
    open/close arrow stays on screen while the tab strip scrolls (the engineer, 2026-11-23)."""
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/sample/pond', {method: 'POST'}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    pg.evaluate("setBottom(true)"); pg.wait_for_timeout(200)
    cdp = ctx.new_cdp_session(pg)
    def touch(kind, x, y):
        cdp.send("Input.dispatchTouchEvent", dict(type=kind, touchPoints=[] if kind == "touchEnd" else [dict(x=x, y=y)]))
    r = pg.evaluate("(() => { const b = document.getElementById('split-bottom').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; })()")
    touch("touchStart", r[0], r[1] + 8); touch("touchEnd", 0, 0); pg.wait_for_timeout(300)   # 8 px off the 6 px bar: the finger-sized area
    assert pg.evaluate("ui.bottomCollapsed") is False
    r = pg.evaluate("(() => { const b = document.getElementById('split-bottom').getBoundingClientRect(); return [b.left + b.width / 2, b.top + b.height / 2]; })()")
    h0 = pg.evaluate("ui.bh"); touch("touchStart", r[0], r[1])
    for k in range(1, 9): touch("touchMove", r[0], r[1] + 20 * k)
    touch("touchEnd", 0, 0); pg.wait_for_timeout(300)
    h = pg.evaluate("ui.bh"); assert 120 <= h < h0 - 80 and pg.evaluate("ui.bottomCollapsed") is False, (h0, h)   # dragged down: smaller, still open
    t = pg.evaluate("document.getElementById('bottom-toggle').getBoundingClientRect().right")
    assert t <= 376, t                                                                 # the arrow stays on screen
    assert errs == [], errs
    ctx.close()


def test_v5_tools_morph_onto_pipes_and_structures(server, browser):
    """The engineer, 2026-11-23: a click with the layout or a structure tool on an existing pipe or structure uses it.
    A run ending on a pipe splits it and joins (one undo step); a wet well on a pipe splits it as a wet well; the pump
    tool turns the manhole it starts on into a wet well."""
    ctx = browser.new_context(viewport={"width": 1600, "height": 950}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.click("#rb-tab-file"); pg.get_by_test_id("rb-new").click(); pg.get_by_test_id("new-name").fill("Morph")
    pg.get_by_test_id("new-crs-mode").select_option("local"); pg.get_by_test_id("new-create").click()
    pg.wait_for_function("window.ed.state.pid && window.ed.state.model && document.body.dataset.pending === '0'")
    pg.click("#rb-tab-layout"); pg.locator("#rb-page-layout .rb-btn", has_text="Layout").first.click()
    pg.select_option("#layout-spacing", "none"); pg.dispatch_event("#layout-spacing", "change")
    click_at(pg, 0, 0); idle(pg); click_at(pg, 200, 0); idle(pg); pg.keyboard.press("Escape")
    assert len(ids(pg, "links")) == 1
    click_at(pg, 100, 80); idle(pg); click_at(pg, 100, 0.5); idle(pg); pg.keyboard.press("Escape")   # the run ends on the pipe
    kinds = pg.evaluate("[...window.ed.state.model.nodes.values()].map(f => f.properties.kind)")
    assert len(ids(pg, "links")) == 3 and len(kinds) == 4 and set(kinds) == {"manhole"}, (ids(pg, "links"), kinds)
    pg.get_by_test_id("qat-undo-btn").click(); idle(pg); assert len(ids(pg, "links")) == 1   # split and pipe: one step
    vtool(pg, "wetwell"); click_at(pg, 50, 0.5); idle(pg)
    sel = pg.evaluate("window.ed.state.sel.ids[0]")
    assert pg.evaluate("id => window.ed.state.model.nodes.get(id).properties.kind", sel) == "wetwell" and len(ids(pg, "links")) == 2
    start = [n for n in ids(pg, "nodes") if pg.evaluate("id => window.ed.state.model.nodes.get(id).geometry.coordinates[1]", n) > 0][0]
    vtool(pg, "pump"); click_at(pg, 100, 80); idle(pg)
    assert pg.evaluate("id => window.ed.state.model.nodes.get(id).properties.kind", start) == "wetwell"
    assert errs == [], errs
    ctx.close()


def test_v5_phone_design_changes_the_elements_and_the_assistants_scenario_opens(server, browser):
    """The engineer, 2026-11-23, on a phone: Design seemed to change nothing (a preview, the old main button), and the
    assistant's changes stayed in a scenario that was not on screen. Design now is the main button and writes sizes and
    levels into the elements and their labels; a preview says it changed nothing and offers Apply; a scenario the
    assistant made is offered with Open it."""
    import json as _json
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/new', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({name: 'phone'})}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    vtool(pg, "manhole")
    for x in (0, 60): click_at(pg, x, 0); idle(pg)
    vtool(pg, "outfall"); click_at(pg, 120, 0); idle(pg)
    vtool(pg, "pipe")
    for a, b in ((0, 60), (60, 120)): click_at(pg, a, 0); idle(pg); click_at(pg, b, 0); idle(pg)
    vtool(pg, "select")
    lab = lambda: pg.evaluate("window.ed.state.model.linkFeat.map(f => f.properties._lab)")
    assert lab() == ["DN200 · 0.00 %"] * 2
    pg.evaluate("openDesignDlg()")
    assert "primary" in pg.get_attribute("#des-run", "class") and "primary" not in (pg.get_attribute("#des-preview", "class") or "")
    pg.click("#des-preview"); idle(pg)
    assert lab() == ["DN200 · 0.00 %"] * 2 and "primary" in pg.get_attribute("#toolout-apply", "class")   # a preview changes nothing
    pg.click("#toolout-apply"); idle(pg)
    assert all(l.endswith("0.50 %") for l in lab()), lab()                                            # applied: laid at the gradient
    assert pg.evaluate("Math.max(...window.ed.state.model.nodeFeat.map(f => -f.properties.invert))") > 1.5
    # the assistant made a scenario while answering: the reply offers it, and Open it puts it on screen
    pid = pg.evaluate("window.ed.state.pid")
    def fake(route):
        req = urllib.request.Request(f"{server}/api/g/projects/{pid}/scenarios/base/copy", data=b'{"name": "made by the assistant"}', headers={"Content-Type": "application/json"}, method="POST")
        urllib.request.urlopen(req).read()
        route.fulfill(status=200, content_type="application/json", body=_json.dumps(dict(reply="Done.", tool_calls=[], usage={}, ui_actions=[])))
    pg.route("**/api/g/assistant", fake)
    pg.evaluate("showTab('assistant'); state.asstOn = true; document.getElementById('asst-input').disabled = false; document.getElementById('asst-input').value = 'make a scenario'; asstSend()")
    pg.wait_for_selector("[data-testid=asst-made-scenario] button"); pg.click("[data-testid=asst-made-scenario] button"); idle(pg)
    assert pg.evaluate("window.ed.state.sid") != "base"
    assert errs == [], errs
    ctx.close()


IBRI_TERRAIN = r"D:\Mojtaba\Renardet\2621 Ibri Sewer STP\Data\Terrain\Sat_0p5m"


@pytest.mark.skipif(not os.path.isdir(IBRI_TERRAIN), reason="the engineer's Ibri terrain is on this computer only")
def test_v5_terrain_read_in_the_browser_matches_the_servers_reading(server, browser):
    """The gate for F28: 200 Ibri structures read in the browser (nothing uploaded) from the 7.4 GB 0.5 m GeoTIFF, the
    5 m GeoTIFF and the VRT over both, against rasterio on the same files. Exact on a GeoTIFF; on the VRT exact where the
    0.5 m source covers, within 1 cm where the 5 m source is resampled bilinearly."""
    import numpy as np
    from sewerapp.io import ibri_sample
    from sewerapp.engine import tools_v4
    p = ibri_sample.build("SC1-2056"); ids = list(p.nodes.index[::max(1, len(p.nodes) // 200)][:200])
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}); pg = ctx.new_page(); pg.set_default_timeout(180000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/sample/SC1-2056', {method: 'POST'}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    pg.evaluate("(() => { const i = document.createElement('input'); i.type = 'file'; i.multiple = true; i.id = 't6-in'; document.body.appendChild(i); })()")
    def browser_levels(names):
        pg.set_input_files("#t6-in", [os.path.join(IBRI_TERRAIN, n) for n in names])
        return pg.evaluate("ids => terrainLevels(document.getElementById('t6-in').files, ids).then(r => r.levels)", ids)
    for names, ref in ((["ibri_0p5_blend.tif"], "ibri_0p5_blend.tif"), (["ibri_blend.tif"], "ibri_blend.tif"),
                       (["IBRI_0p5_VRT2.vrt", "ibri_blend.tif", "ibri_0p5_blend.tif"], "IBRI_0p5_VRT2.vrt")):
        got = browser_levels(names); want, bad = tools_v4.trex(p, os.path.join(IBRI_TERRAIN, ref), ids)
        both = [i for i in ids if got.get(i) is not None and i in want]
        assert len(both) >= 0.9 * len(want) and not [i for i in want if got.get(i) is None], (names, len(both), len(want))
        d = np.array([got[i] - want[i] for i in both])
        tol = 1e-6 if ref.endswith(".tif") else 0.01
        assert np.abs(d).max() <= tol, (names, float(np.abs(d).max()), int((np.abs(d) > tol).sum()))
    # a VRT without its files names what is missing
    pg.set_input_files("#t6-in", [os.path.join(IBRI_TERRAIN, "IBRI_0p5_VRT2.vrt")])
    msg = pg.evaluate("ids => terrainLevels(document.getElementById('t6-in').files, ids).then(() => '', e => e.message)", ids[:3])
    assert "ibri_blend.tif" in msg and "ibri_0p5_blend.tif" in msg, msg
    assert errs == [], errs
    ctx.close()


def test_v5_trex_dialog_reads_a_picked_geotiff_and_keeps_its_source(server, browser, tmp_path):
    """F28 in the dialog: Choose files... (a GeoTIFF on this device, read here), Apply, the ground and its source in
    Properties; Copernicus offered for a project in a real CRS; on a phone a VRT is said not to work."""
    import json as _json, numpy as np, rasterio
    from rasterio.transform import from_origin
    tif = str(tmp_path / "dem.tif")
    with rasterio.open(tif, "w", driver="GTiff", width=100, height=100, count=1, dtype="float32", crs="EPSG:32640", tiled=True, blockxsize=32, blockysize=32,
                       transform=from_origin(445000, 2565100, 2, 2), nodata=-9999) as d:
        d.write(np.fromfunction(lambda r, c: 300 + c * 0.1, (100, 100), dtype=float).astype("float32"), 1)
    def post(path, body):
        req = urllib.request.Request(server + "/api/g" + path, data=_json.dumps(body).encode(), headers={"Content-Type": "application/json"}, method="POST")
        return _json.loads(urllib.request.urlopen(req).read())
    info = post("/projects/new", dict(name="terrain", crs=32640)); B = f"/projects/{info['id']}/scenarios/base/edit"
    post(B, dict(op="add_node", id="A", x=445021.0, y=2565001.0)); post(B, dict(op="add_node", id="B", kind="outfall", x=445101.0, y=2565001.0))
    post(B, dict(op="add_link", id="P", from_node="A", to_node="B"))
    ctx = browser.new_context(viewport={"width": 1400, "height": 900}); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate(f"jget('/projects/{info['id']}').then(i => openProject(i))"); idle(pg)
    pg.evaluate("openTRex()")
    assert pg.is_enabled("[data-testid=trex-cop]") and "DLR" in pg.inner_text("#dlg-trex")
    with pg.expect_file_chooser() as fc: pg.click("[data-testid=trex-files]")
    fc.value.set_files(tif)
    pg.click("#dlg-trex [data-act=ok]"); pg.wait_for_selector("[data-testid=trex-done]"); idle(pg)
    a = pg.evaluate("window.ed.state.model.nodes.get('A').properties")
    assert abs(a["ground"] - (300 + 10 * 0.1)) < 1e-4 and a["ground_src"] == "file dem.tif, 2 m cells", a   # column 10 of the grid
    assert abs(a["invert"] - (a["ground"] - 1.5)) < 1e-6                                                   # the depth kept
    pg.evaluate("document.getElementById('dlg-trex').hidden = true; window.ed.selectElement('nodes', 'A')")
    expect(pg.locator("#prop-ground_src")).to_have_value("file dem.tif, 2 m cells")
    pg.evaluate("delete window.showDirectoryPicker; window.matchMedia = q => ({ matches: /coarse/.test(q), addEventListener() {}, removeEventListener() {} }); openTRex()")
    expect(pg.get_by_test_id("trex-phone")).to_be_visible()
    assert errs == [], errs
    ctx.close()


def test_v5_map_has_a_north_arrow_and_fit_all(server, browser):
    """The engineer, 2026-11-23, on a phone: a rotated map needs a north arrow to put north up again, and the map box
    needs Fit all to find the pipes."""
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, has_touch=True, is_mobile=True); pg = ctx.new_page(); pg.set_default_timeout(60000); errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(server + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    pg.evaluate("fetch('/api/g/projects/sample/pond', {method: 'POST'}).then(r => r.json()).then(i => openProject(i))"); idle(pg)
    pg.evaluate("window.ed.map.jumpTo({ center: [10, 10], zoom: 3, bearing: 40 })")
    expect(pg.locator(".maplibregl-ctrl-compass")).to_be_visible(); expect(pg.get_by_test_id("map-fit")).to_be_visible()
    pg.click(".maplibregl-ctrl-compass"); pg.wait_for_function("Math.abs(window.ed.map.getBearing()) < 0.01")
    pg.click("[data-testid=map-fit]"); pg.wait_for_timeout(300)
    inside = pg.evaluate("(() => { const b = window.ed.map.getBounds(); return window.ed.state.model.nodeFeat.every(f => b.contains(f.geometry.coordinates)); })()")
    assert inside and pg.evaluate("window.ed.map.getZoom()") > 10
    assert errs == [], errs
    pg.screenshot(path=os.path.join(SHOTS, "screenshot_v5_compass_fit.png")); ctx.close()
