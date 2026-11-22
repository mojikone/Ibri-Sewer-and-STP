"""End-to-end tests of the browser interface (Playwright, system Chrome) against a live server on port 8799."""
import os, subprocess, sys, time, urllib.request
import pytest
from playwright.sync_api import sync_playwright, expect

W19 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PORT = 8799
URL = f"http://127.0.0.1:{PORT}"


@pytest.fixture(scope="module")
def server():
    env = dict(os.environ, W19_ASSISTANT_STUB="1")
    p = subprocess.Popen([sys.executable, "-c", f"import uvicorn; uvicorn.run('sewerapp.api.app:app', host='127.0.0.1', port={PORT})"],
                         cwd=W19, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while True:
            try:
                urllib.request.urlopen(URL + "/api/scenarios", timeout=2)
                break
            except Exception:
                if p.poll() is not None:
                    raise RuntimeError("server exited")
                if time.time() - t0 > 120:
                    raise RuntimeError("server did not start")
                time.sleep(0.5)
        yield URL
    finally:
        p.terminate()
        try:
            p.wait(10)
        except Exception:
            p.kill()


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch(channel="chrome", headless=True)
        yield b
        b.close()


@pytest.fixture(scope="module")
def page(server, browser):
    ctx = browser.new_context(viewport={"width": 1500, "height": 900}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(60000)
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(server + "/")
    pg.wait_for_function("window.app && window.app.state.ready", timeout=120000)
    yield pg
    ctx.close()


def relay(page):
    return int(page.locator("#status-line").get_attribute("data-relay"))


def seconds(page):
    return float(page.locator("#status-line").get_attribute("data-seconds"))


def test_01_loads_and_reports_pipes(page):
    expect(page.locator("#status-line")).to_contain_text("19,083 pipes")
    assert relay(page) == 0
    assert page.locator("#scenario-select").input_value().startswith("SC1")
    assert page.locator("#scenario-select option").count() >= 12


def test_02_map_has_pipes_source(page):
    assert page.evaluate("window.app.state.pipeFeatures") == 19083
    assert page.evaluate("window.app.map.getSource('pipes')._data.features.length") == 19083
    assert page.evaluate("window.app.map.getLayer('pipes-base') !== undefined")
    assert page.locator("#legend").inner_text().strip() != ""


def test_03_select_pipe_fills_grid_readonly_base(page):
    page.evaluate("window.app.selectPipe(100)")
    expect(page.locator("#props")).to_contain_text("From manhole")
    assert page.locator("#prop-dn").is_disabled()
    assert page.locator("#prop-s").is_disabled()
    expect(page.locator("#readonly-hint")).to_be_visible()
    assert page.locator("#prop-dn").input_value().isdigit()


def test_04_copy_to_whatif(page):
    n0 = page.locator("#scenario-select option").count()
    page.click("#copy-btn")
    page.wait_for_function("window.app.state.sid && window.app.state.sid.startsWith('W')")
    assert page.locator("#scenario-select option").count() == n0 + 1
    assert "what-if" in page.locator("#scenario-select option:checked").inner_text()
    expect(page.locator("#readonly-hint")).to_be_hidden()
    assert page.evaluate("window.app.state.scenarios.find(s => s.id === window.app.state.sid).read_only") is False


def test_05_edit_dn_resolves_instantly(page):
    page.evaluate("window.app.selectPipe(100)")
    expect(page.locator("#prop-dn")).to_be_enabled()
    assert relay(page) == 0
    cur = page.locator("#prop-dn").input_value()
    new = "250" if cur != "250" else "315"
    page.select_option("#prop-dn", new)
    page.wait_for_function("+document.getElementById('status-line').dataset.relay > 0")
    assert relay(page) > 0
    assert seconds(page) < 1.0
    expect(page.locator("#status-line")).to_contain_text("re-solved")
    assert page.locator("#prop-dn").input_value() == new
    assert page.locator("#undo-btn").is_enabled()
    assert page.evaluate("window.app.map.getSource('pipes')._data.features.filter(f => f.properties.relay === 1).length") > 0


def test_06_undo_redo(page):
    page.click("#undo-btn")
    page.wait_for_function("+document.getElementById('status-line').dataset.relay === 0")
    assert relay(page) == 0 and page.locator("#redo-btn").is_enabled() and page.locator("#undo-btn").is_disabled()
    page.click("#redo-btn")
    page.wait_for_function("+document.getElementById('status-line').dataset.relay > 0")
    assert relay(page) > 0


def test_07_bulk_edit_two_pipes(page):
    page.evaluate("window.app.selectPipe(200)")
    page.evaluate("window.app.selectPipe(201, {add: true})")
    expect(page.locator("#props")).to_contain_text("2 pipes selected")
    before = relay(page)
    page.fill("#prop-s", "0.9")
    page.press("#prop-s", "Enter")
    page.wait_for_function(f"+document.getElementById('status-line').dataset.relay !== {before}")
    cols = page.evaluate("window.app.state.results.columns.s_pc")
    assert abs(cols[200] - 0.9) < 1e-6 and abs(cols[201] - 0.9) < 1e-6
    page.click("#undo-btn")
    page.wait_for_function(f"+document.getElementById('status-line').dataset.relay === {before}")


def test_08_results_table(page):
    page.click("#tab-results")
    assert page.locator("#results-table tbody tr").count() == 200
    page.fill("#results-filter", page.evaluate("window.app.state.props ? window.app.state.props.label : ''") or "")
    assert page.locator("#results-table tbody tr").count() >= 1
    page.fill("#results-filter", "")
    page.locator("#results-table th[data-col=dn_mm]").click()
    page.locator("#results-table tbody tr").nth(5).click()
    page.wait_for_function("window.app.state.selected.length === 1")
    expect(page.locator("#props")).to_contain_text("From manhole")


def test_09_profile_svg(page):
    page.evaluate("window.app.selectPipe(100)")
    page.click("#tab-profile")
    page.click("#profile-run")
    page.wait_for_function("document.querySelectorAll('#profile-svg .pipe-seg').length >= 3")
    assert page.locator("#profile-svg .pipe-seg").count() >= 3
    assert page.locator("#profile-svg .pipe-seg.relay").count() >= 1


def test_10_export_gpkg_download(page, tmp_path):
    page.click("#export-btn")
    with page.expect_download(timeout=120000) as dl:
        page.click("#export-gpkg")
    f = tmp_path / "x.gpkg"
    dl.value.save_as(str(f))
    assert f.stat().st_size > 100_000


def test_11_tools_failing_pipes(page):
    page.click("#tools-menu")
    page.click("#tools-list button.item[data-tool=checks]")
    page.wait_for_function("document.querySelector('#tool-output table') !== null")
    assert page.locator("#tool-output table tbody tr").count() >= 1
    expect(page.locator("#tool-title")).to_contain_text("Failing pipes")


def test_12_compare(page):
    page.select_option("#compare-select", "SC1-2056")
    page.wait_for_function("document.querySelector('#compare-table') !== null || document.querySelector('#compare-output').innerText.includes('No rows')")
    expect(page.locator("#compare-title")).to_contain_text("changed")


def test_13_colour_by_and_basemap(page):
    page.select_option("#color-by", "v_ms")
    assert "Velocity" in page.locator("#legend").inner_text()
    page.select_option("#color-by", "failing")
    assert page.evaluate("new Set(window.app.map.getSource('pipes')._data.features.map(f => f.properties.c)).size") <= 2
    page.uncheck("#basemap-toggle")
    assert page.evaluate("window.app.map.getLayoutProperty('osm', 'visibility')") == "none"
    page.check("#basemap-toggle")
    page.select_option("#color-by", "dn_mm")


def test_14_assistant_stub(page):
    page.click("#tab-assistant")
    page.wait_for_function("!document.getElementById('assistant-input').disabled", timeout=10000)
    page.fill("#assistant-input", "How many pipes fail in this scenario?")
    page.click("#assistant-send")
    page.wait_for_function("document.querySelectorAll('#assistant-log .msg.bot').length >= 1 && !document.querySelector('#assistant-log').innerText.includes('thinking')")
    assert len(page.locator("#assistant-log").inner_text().strip()) > 20
    assert page.locator("#assistant-log .toolcalls").count() >= 1


def test_15_screenshot_and_no_js_errors(page):
    page.select_option("#scenario-select", "SC1-2056")
    page.wait_for_function("window.app.state.sid === 'SC1-2056' && +document.getElementById('status-line').dataset.relay === 0")
    page.evaluate("window.app.selectPipe(100, {zoom: true})")
    page.click("#tab-profile")
    page.click("#profile-run")
    page.wait_for_function("document.querySelectorAll('#profile-svg .pipe-seg').length >= 3")
    page.wait_for_timeout(1500)
    out = os.path.join(W19, "work", "screenshot_app.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    page.screenshot(path=out)
    assert os.path.getsize(out) > 20_000
    assert not page.errors, page.errors
