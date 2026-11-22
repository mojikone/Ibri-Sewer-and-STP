"""End-to-end tests of the general network editor (web/editor) in system Chrome against a live server on port 8798."""
import os, subprocess, sys, time, urllib.request
import pytest
from playwright.sync_api import sync_playwright, expect

W19 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PORT = 8798
URL = f"http://127.0.0.1:{PORT}"
M_LON, M_LAT = 111319.49, 110574.0          # local-metre projects: degrees <-> metres (api/coords.py)
EXTRAN1 = os.path.join(W19, "tests", "fixtures", "swmm", "extran", "extran1.inp")
SHOTS = os.path.join(W19, "work")


@pytest.fixture(scope="module")
def server():
    p = subprocess.Popen([sys.executable, "-c", "import uvicorn; uvicorn.run('sewerapp.api.app:app', host='127.0.0.1', port=8798)"],
                         cwd=W19, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
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


def new_local(pg, name="Test"):
    pg.get_by_test_id("new-btn").click()
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
    page.get_by_test_id("sample-btn").click()
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
        page.get_by_test_id("export-btn").click()
    f = str(tmp_path / "model.inp"); d.value.save_as(f)
    assert "[CONDUITS]" in open(f, encoding="utf-8", errors="ignore").read()


def test_no_javascript_errors(page):
    assert page.errors == [], page.errors
