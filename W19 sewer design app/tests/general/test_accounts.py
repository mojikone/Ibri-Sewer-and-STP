"""Accounts (2026-11-24 v8): the signed-in identity from Cloudflare Access's token, projects per account, the admin,
the assistant per account and limited to the caller's projects, accounts off = as before."""
import json, time
import jwt, pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi.testclient import TestClient
from sewerapp.api.app import app
from sewerapp.api import accounts, general_api as G
from sewerapp.assistant import budget

C = TestClient(app)
TEAM, AUD = "https://test-team.cloudflareaccess.com", "aud-tag-1"
KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
OTHER = rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _jwks(key, kid):
    d = json.loads(jwt.algorithms.RSAAlgorithm.to_jwk(key.public_key())); d.update(kid=kid, alg="RS256", use="sig")
    return {"keys": [d]}


def token(email, aud=AUD, iss=TEAM, exp=300, key=KEY, kid="k1"):
    now = int(time.time())
    return jwt.encode(dict(email=email, aud=[aud], iss=iss, iat=now, nbf=now, exp=now + exp, sub="x"), key, algorithm="RS256", headers={"kid": kid})


def web(email=None, **kw):
    h = {"cf-connecting-ip": "203.0.113.9"}
    if email: h["cf-access-jwt-assertion"] = token(email, **kw)
    return h


@pytest.fixture
def acc(tmp_path, monkeypatch):
    (tmp_path / "jwks.json").write_text(json.dumps(_jwks(KEY, "k1")))
    (tmp_path / "access.json").write_text(json.dumps(dict(team=TEAM, aud=AUD, admins=["Boss@Example.com"], jwks_file="jwks.json")))
    monkeypatch.setenv("W19_ACCESS_CONFIG", str(tmp_path / "access.json"))
    monkeypatch.setenv("W19_ACCOUNTS_DIR", str(tmp_path / "accounts"))
    accounts._st.update(index=None); accounts._cfg.update(key=None)
    monkeypatch.setattr(budget, "LIMITS_FILE", str(tmp_path / "limits.json")); monkeypatch.setattr(budget, "LEDGER_FILE", str(tmp_path / "ledger.json"))
    yield tmp_path
    accounts._st.update(index=None); accounts._cfg.update(key=None)


def _new(h, name="mine"):
    r = C.post("/api/g/projects/new", json=dict(name=name, crs=32640), headers=h); assert r.status_code == 200, r.text
    return r.json()["id"]


def test_over_the_web_a_valid_sign_in_is_needed(acc):
    assert C.get("/api/g/me", headers=web()).status_code == 401                                   # none
    assert C.get("/api/g/me", headers=web("a@x.com", key=OTHER)).status_code == 401              # forged signature
    assert C.get("/api/g/me", headers=web("a@x.com", aud="another-app")).status_code == 401      # another Access app
    assert C.get("/api/g/me", headers=web("a@x.com", iss="https://evil.cloudflareaccess.com")).status_code == 401
    assert C.get("/api/g/me", headers=web("a@x.com", exp=-120)).status_code == 401                # expired
    assert C.get("/api/g/me", headers={**web(), "cf-access-authenticated-user-email": "boss@example.com"}).status_code == 401   # a plain header is never trusted
    me = C.get("/api/g/me", headers=web("A@X.com")).json()
    assert me["mode"] == "user" and me["email"] == "a@x.com" and not me["admin"] and me["accounts"]
    assert C.get("/api/g/me", headers=web("boss@example.com")).json()["admin"]
    assert C.get("/api/g/me").json()["mode"] == "local"                                           # this computer: no sign-in
    h = {"cf-connecting-ip": "203.0.113.9", "cookie": "CF_Authorization=" + token("c@x.com")}      # the cookie works too
    assert C.get("/api/g/me", headers=h).json()["email"] == "c@x.com"


def test_each_account_has_its_own_projects(acc):
    A, B, boss = web("a@x.com"), web("b@x.com"), web("boss@example.com")
    pa = _new(A, "A's"); pb = _new(B, "B's"); pl = _new({}, "this computer's")
    assert [p["id"] for p in C.get("/api/g/projects", headers=A).json()] == [pa]
    assert [p["name"] for p in C.get("/api/g/projects", headers=B).json()] == ["B's"]
    assert C.get(f"/api/g/projects/{pa}", headers=A).status_code == 200
    for path in (f"/api/g/projects/{pa}", f"/api/g/projects/{pa}/scenarios/base/model", f"/api/g/projects/{pl}"):
        r = C.get(path, headers=B); assert r.status_code == 403 and "another account" in r.text, path
    r = C.post(f"/api/g/projects/{pa}/scenarios/base/edit", json=dict(op="add_node", id="M1", x=57.0, y=23.2), headers=B)
    assert r.status_code == 403
    assert C.get(f"/api/g/projects/{pa}", headers=boss).status_code == 200                        # the admin opens any
    assert C.get(f"/api/g/projects/{pl}", headers=boss).status_code == 200
    assert C.get(f"/api/g/projects/{pa}").status_code == 200                                      # and so does this computer
    assert C.get("/api/g/projects/pdeadbeef", headers=A).status_code == 404                       # unknown stays unknown
    users = C.get("/api/g/admin/users", headers=boss).json()
    assert {u["email"] for u in users} >= {"a@x.com", "b@x.com"} and C.get("/api/g/admin/users", headers=A).status_code == 403


def test_a_project_is_removed_only_by_its_account(acc):
    A, B = web("a@x.com"), web("b@x.com"); pa = _new(A)
    assert C.post(f"/api/g/projects/{pa}/delete", headers=B).status_code == 403
    assert C.post(f"/api/g/projects/{pa}/delete", headers=A).status_code == 200
    assert C.get("/api/g/projects", headers=A).json() == [] and C.get(f"/api/g/projects/{pa}", headers=A).status_code == 404


def test_an_accounts_projects_are_kept_on_the_server(acc, monkeypatch):
    monkeypatch.setattr(G, "AUTOSAVE", str(acc / "sessions"))
    A = web("a@x.com"); pa = _new(A, "kept")
    f = G.snapshot(pa); uid = accounts.uid_of("a@x.com")
    assert f.startswith(str(acc / "accounts" / uid)) and (acc / "accounts" / uid / "account.json").exists()
    G.SESSIONS.pop(pa); accounts._st.update(index=None)                                           # a restart
    assert C.get(f"/api/g/projects/{pa}", headers=A).json()["name"] == "kept"
    assert C.get(f"/api/g/projects/{pa}", headers=web("b@x.com")).status_code == 403
    G._init_autosave()                                                                             # the clean-up never touches it
    assert (acc / "accounts" / uid / f"{pa}.pkl").exists()


def test_the_assistant_spends_and_sees_per_account(acc, monkeypatch):
    from sewerapp.assistant import gtools
    A, B = web("a@x.com"), web("b@x.com"); pa = _new(A, "A's"); pb = _new(B, "B's")
    tok = G.WHO.set(dict(kind="user", email="a@x.com", uid=accounts.uid_of("a@x.com"), admin=False))
    try:
        ids = [p["id"] for p in gtools.call(None, "list_projects", {})]
        assert pa in ids and pb not in ids
        with pytest.raises(ValueError): gtools.call(None, "project_summary", dict(project=pb, scenario="base"))
    finally: G.WHO.reset(tok)
    monkeypatch.setenv("W19_ASSISTANT_STUB", "1")
    r = C.post("/api/g/assistant", json=dict(project=pb, scenario="base", message="how many pipes?"), headers=A)
    assert r.status_code == 403
    r = C.post("/api/g/assistant", json=dict(project=pa, scenario="base", message="how many pipes?"), headers=A)
    assert r.status_code == 200, r.text
    led = json.loads((acc / "ledger.json").read_text())["days"]
    assert any(k == "web:" + accounts.uid_of("a@x.com") for d in led.values() for k in d)


def test_accounts_off_is_as_before(tmp_path, monkeypatch):
    monkeypatch.delenv("W19_ACCESS_CONFIG", raising=False); accounts._cfg.update(key=None)
    V = {"cf-connecting-ip": "203.0.113.9"}
    assert C.get("/api/g/me", headers=V).json()["mode"] == "anon"
    p = _new(V); assert C.get("/api/g/projects", headers=V).json() == []
    assert C.get(f"/api/g/projects/{p}", headers={"cf-connecting-ip": "198.51.100.1"}).status_code == 200    # by its link
    assert C.post(f"/api/g/projects/{p}/delete", headers=V).status_code == 403
