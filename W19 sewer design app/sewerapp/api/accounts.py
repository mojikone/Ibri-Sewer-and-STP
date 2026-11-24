"""Accounts (v8, 2026-11-24): who is using the app over the web, and the projects each account owns.

The sign-in itself is Cloudflare Access's (Google, one-time code by email, or any identity provider set there): it puts a
signed token on every request that reaches the app through the shared address (header Cf-Access-Jwt-Assertion, cookie
CF_Authorization). The app checks that token's signature against the team's public keys, its audience (the Access
application's AUD tag) and its issuer, and takes the email from it; an unsigned or forged email header is never trusted.

The configuration is a small JSON file outside the repository (W19_ACCESS_CONFIG; `python -m sewerapp.api` looks in the
server's own folder): {"team": "https://<team>.cloudflareaccess.com", "aud": "<AUD tag>", "admins": ["<email>"]}.
Without it the app works as before accounts: a web visitor is anonymous and keeps its projects in its own browser.

Three kinds of caller: "local" (a page opened on this computer: everything, no sign-in), "user" (signed in over the web:
its own projects; an admin opens any) and "anon" (over the web with accounts off). An account's projects are kept under
W19_ACCOUNTS_DIR/<uid>/ (outside the repository: it holds email addresses), never cleared by the autosave's clean-up."""
import hashlib, json, os, threading, time

LOCAL = dict(kind="local", email=None, uid=None, admin=True)
ANON = dict(kind="anon", email=None, uid=None, admin=False)


class Unauthorized(Exception):
    pass


# ---- configuration (re-read when the file changes)
_cfg = {"key": None, "val": None}


def config():
    p = os.environ.get("W19_ACCESS_CONFIG")
    if not p or not os.path.exists(p): return None
    key = (p, os.path.getmtime(p))
    if _cfg["key"] != key:
        with open(p, encoding="utf-8-sig") as f: c = json.load(f)
        team, aud = str(c.get("team") or "").strip().rstrip("/"), c.get("aud")
        if not team or not aud: raise ValueError(f"{p}: 'team' and 'aud' are both needed")
        if not team.startswith("https://"): team = "https://" + team
        jw = c.get("jwks_file")
        if jw and not os.path.isabs(jw): jw = os.path.join(os.path.dirname(p), jw)
        _cfg.update(key=key, val=dict(team=team, aud=aud if isinstance(aud, list) else [aud],
                                     admins={str(a).strip().lower() for a in c.get("admins") or []}, jwks_file=jw))
    return _cfg["val"]


def on():
    return config() is not None


# ---- the signed sign-in
_jwk_clients: dict = {}


def _key(token, c):
    import jwt
    if c.get("jwks_file"):                                  # tests: the team's keys from a file instead of the network
        with open(c["jwks_file"], encoding="utf-8") as f: ks = jwt.PyJWKSet.from_dict(json.load(f))
        kid = jwt.get_unverified_header(token).get("kid")
        for k in ks.keys:
            if k.key_id == kid: return k.key
        raise Unauthorized("the sign-in was signed with an unknown key")
    url = c["team"] + "/cdn-cgi/access/certs"
    if url not in _jwk_clients: _jwk_clients[url] = jwt.PyJWKClient(url, cache_keys=True, lifespan=3600)
    return _jwk_clients[url].get_signing_key_from_jwt(token).key


def verify(token):
    """The signed-in email from Cloudflare Access's token, or Unauthorized."""
    import jwt
    c = config()
    try:
        claims = jwt.decode(token, _key(token, c), algorithms=["RS256"], audience=c["aud"], issuer=c["team"], leeway=30)
    except Unauthorized: raise
    except Exception as e: raise Unauthorized(f"the sign-in could not be checked ({type(e).__name__}): sign in again through the site's address")
    email = str(claims.get("email") or "").strip().lower()
    if not email: raise Unauthorized("the sign-in carries no email address")
    return email


def uid_of(email):
    return "u" + hashlib.sha256(email.strip().lower().encode()).hexdigest()[:16]


def identity(headers, cookies, remote):
    """Who is calling: LOCAL, ANON, or a signed-in user (dict with email, uid, admin). Unauthorized over the web when
    accounts are on and the request carries no valid sign-in."""
    if not remote: return LOCAL
    c = config()
    if c is None: return ANON
    tok = headers.get("cf-access-jwt-assertion") or cookies.get("CF_Authorization")
    if not tok: raise Unauthorized("sign in through the site's address first")
    email = verify(tok)
    return dict(kind="user", email=email, uid=uid_of(email), admin=email in c["admins"])


# ---- the registry: accounts and the projects they own
_lock = threading.RLock()
_st = {"dir": None, "index": None, "acc": None, "saved": {}}


def _dir():
    return os.environ.get("W19_ACCOUNTS_DIR")


def _load():
    d = _dir()
    if _st["index"] is not None and _st["dir"] == d: return
    idx, acc = {}, {}
    if d and os.path.isdir(d):
        for u in os.listdir(d):
            f = os.path.join(d, u, "account.json")
            if os.path.exists(f):
                try:
                    with open(f, encoding="utf-8") as h: acc[u] = json.load(h)
                except (OSError, ValueError): continue
                for pid in acc[u].get("projects", {}): idx[pid] = u
    _st.update(dir=d, index=idx, acc=acc, saved={})


def _save(uid, force=True):
    d = _dir()
    if not d or uid not in _st["acc"]: return
    if not force and time.time() - _st["saved"].get(uid, 0) < 60: return
    os.makedirs(os.path.join(d, uid), exist_ok=True)
    f = os.path.join(d, uid, "account.json"); tmp = f + ".tmp"
    with open(tmp, "w", encoding="utf-8") as h: json.dump(_st["acc"][uid], h, indent=1)
    os.replace(tmp, f); _st["saved"][uid] = time.time()


def touch(who):
    """Note a signed-in user's visit (its account is made on the first one)."""
    if who.get("kind") != "user": return
    with _lock:
        _load(); new = who["uid"] not in _st["acc"]
        a = _st["acc"].setdefault(who["uid"], dict(email=who["email"], first=time.time(), projects={}))
        a["last"] = time.time(); a["email"] = who["email"]
        _save(who["uid"], force=new)


def own(pid, who, name):
    """A project just made by a signed-in user becomes that account's."""
    if who.get("kind") != "user": return
    with _lock:
        touch(who); _st["index"][pid] = who["uid"]
        _st["acc"][who["uid"]]["projects"][pid] = dict(name=name, t=time.time())
        _save(who["uid"])


def owner(pid):
    with _lock:
        _load(); return _st["index"].get(pid)


def note(pid, name):
    """A project's name and time of change, when its snapshot is written."""
    with _lock:
        _load(); u = _st["index"].get(pid)
        if not u: return
        p = _st["acc"][u]["projects"].get(pid)
        if p is not None and (p.get("name") != name or time.time() - p.get("t", 0) > 60):
            p.update(name=name, t=time.time()); _save(u)


def drop(pid):
    with _lock:
        _load(); u = _st["index"].pop(pid, None)
        if u:
            _st["acc"][u]["projects"].pop(pid, None); _save(u)
            f = snap_path(pid, u)
            if f and os.path.exists(f): os.remove(f)


def snap_path(pid, uid=None):
    """Where an owned project's snapshot is kept (None: not owned, or no accounts folder)."""
    u = uid or owner(pid); d = _dir()
    return os.path.join(d, u, f"{pid}.pkl") if (u and d) else None


def projects(uid):
    with _lock:
        _load(); P = (_st["acc"].get(uid) or {}).get("projects", {})
        return sorted((dict(id=k, name=v.get("name"), t=v.get("t")) for k, v in P.items()), key=lambda r: -(r["t"] or 0))


def users():
    with _lock:
        _load()
        return sorted((dict(uid=u, email=a.get("email"), first=a.get("first"), last=a.get("last"), projects=projects(u))
                       for u, a in _st["acc"].items()), key=lambda r: -(r["last"] or 0))


def can_open(pid, who, exists=True):
    """local: any project; anon (accounts off): any, by its link, as before; a user: its own, an admin any. A project
    no account owns (made on this computer, or before accounts) is the engineer's."""
    k = who.get("kind")
    if k in ("local", "anon"): return True
    if who.get("admin"): return True
    u = owner(pid)
    return u == who["uid"] or (u is None and not exists)
