"""Accounts in the browser (2026-11-24 v8): a server with accounts on, pages that arrive as Cloudflare Access sends them
(a signed sign-in on every request), each with its email and Sign out, My projects from the server, the admin's Users."""
import json, os, subprocess, sys, time, urllib.request
import jwt, pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from playwright.sync_api import sync_playwright, expect

W19 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PORT = 8796
URL = f"http://127.0.0.1:{PORT}"
TEAM, AUD = "https://test-team.cloudflareaccess.com", "aud-tag-e2e"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def token(email):
    now = int(time.time())
    return jwt.encode(dict(email=email, aud=[AUD], iss=TEAM, iat=now, nbf=now, exp=now + 3600), KEY, algorithm="RS256", headers={"kid": "k1"})


def signed(email): return {"cf-connecting-ip": "203.0.113.20", "cf-access-jwt-assertion": token(email)}


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    d = tmp_path_factory.mktemp("acc")
    k = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(KEY.public_key())); k.update(kid="k1", alg="RS256", use="sig")
    (d / "jwks.json").write_text(json.dumps({"keys": [k]}))
    (d / "access.json").write_text(json.dumps(dict(team=TEAM, aud=AUD, admins=["boss@example.com"], jwks_file="jwks.json")))
    env = dict(os.environ, W19_ASSISTANT_STUB="1", W19_ACCESS_CONFIG=str(d / "access.json"), W19_ACCOUNTS_DIR=str(d / "accounts"),
               W19_AUTOSAVE_DIR=str(d / "sessions"))
    p = subprocess.Popen([sys.executable, "-c", f"import uvicorn; uvicorn.run('sewerapp.api.app:app', host='127.0.0.1', port={PORT})"],
                         cwd=W19, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        t0 = time.time()
        while True:
            try: urllib.request.urlopen(URL + "/api/g/samples", timeout=2); break
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


def open_as(browser, email, path="/v2"):
    ctx = browser.new_context(viewport={"width": 1600, "height": 950})
    h = signed(email)                                                   # as Cloudflare adds it: on the app's own requests only
    ctx.route(URL + "/**", lambda route: route.continue_(headers={**route.request.headers, **h}))
    pg = ctx.new_page(); pg.set_default_timeout(60000); pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(URL + path); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    return ctx, pg


def test_a_signed_in_user_sees_its_email_and_its_own_projects(server, browser):
    ctx, pg = open_as(browser, "ann@example.com")
    try:
        expect(pg.get_by_test_id("me-chip")).to_have_text("ann@example.com")
        expect(pg.get_by_test_id("sign-out")).to_have_attribute("href", "/cdn-cgi/access/logout")
        expect(pg.get_by_test_id("me-users")).to_have_count(0)
        pid = pg.evaluate("async () => (await jpost('/projects/new', {name: 'Ann network', crs: 32640})).id")
        pg.locator("#rb-tab-file").click()
        expect(pg.locator("#rb-recent")).to_contain_text("My projects")
        pg.locator("#rb-recent").click()
        expect(pg.get_by_test_id("mine-" + pid)).to_have_text("Ann network")
        pg.get_by_test_id("mine-" + pid).click()
        pg.wait_for_function(f"state.pid === '{pid}'")
        assert not pg.errors, pg.errors
    finally: ctx.close()
    ctx, pg = open_as(browser, "bob@example.com")                       # another account: not in its list, not by its link
    try:
        pg.locator("#rb-tab-file").click(); pg.locator("#rb-recent").click()
        expect(pg.locator("#dlg-mine")).to_contain_text("None yet")
        r = pg.evaluate(f"async () => {{ try {{ await jget('/projects/{pid}'); return 'opened'; }} catch (e) {{ return e.message; }} }}")
        assert "another account" in r
    finally: ctx.close()
    ctx, pg = open_as(browser, "boss@example.com")                      # the admin: Users, and any project
    try:
        pg.get_by_test_id("me-users").click()
        expect(pg.get_by_test_id("users-table")).to_contain_text("ann@example.com")
        expect(pg.get_by_test_id("users-table")).to_contain_text("Ann network")
        pg.locator("#dlg-users").get_by_role("button", name="Ann network").click()
        pg.wait_for_function(f"state.pid === '{pid}'")
    finally: ctx.close()
    ctx, pg = open_as(browser, "ann@example.com")                       # removed with two clicks
    try:
        pg.locator("#rb-tab-file").click(); pg.locator("#rb-recent").click()
        pg.get_by_test_id("mine-del-" + pid).click(); pg.get_by_test_id("mine-del-" + pid).click()
        expect(pg.locator("#dlg-mine")).to_contain_text("None yet")
    finally: ctx.close()


def test_this_computer_needs_no_sign_in(server, browser):
    ctx = browser.new_context(viewport={"width": 1600, "height": 950})
    pg = ctx.new_page(); pg.goto(URL + "/v2"); pg.wait_for_function("window.ed && window.ed.ribbon === true && window.ed.map")
    try:
        expect(pg.get_by_test_id("me-chip")).to_have_text("This computer")
        expect(pg.get_by_test_id("sign-out")).to_have_count(0)
        assert pg.evaluate("document.body.dataset.me") == "local"
    finally: ctx.close()
