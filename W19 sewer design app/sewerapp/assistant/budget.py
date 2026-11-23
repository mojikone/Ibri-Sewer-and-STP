"""The assistant's spending limit (2026-11-23 v5): what each client may spend on the Claude API per day, kept on this
computer. Until user accounts exist a client is this computer ("local") or one visitor of the shared web link, told
apart by the address Cloudflare reports ("web:<ip>"); all web visitors together have a daily limit too.

Cost is estimated from the token counts each API response reports, at the list prices of the model asked for
(per million tokens, Claude API list prices cached 2026-11-03; a request served by a fallback model is counted at
the asked model's prices). Limits and the ledger are JSON files beside the assistant's folder list; the limits are
changed only from this computer."""
import datetime as dt, json, os, threading

HOME = os.path.join(os.path.expanduser("~"), ".w19")
LIMITS_FILE = os.environ.get("W19_ASSISTANT_LIMITS") or os.path.join(HOME, "assistant_limits.json")
LEDGER_FILE = os.environ.get("W19_ASSISTANT_LEDGER") or os.path.join(HOME, "assistant_usage.json")
# USD per million tokens: input, output, cache write (5 min, 1.25 x input), cache read
PRICES = {"claude-opus-5-5": (4.0, 20.0, 5.0, 0.20), "claude-sonnet-5-5": (2.0, 10.0, 2.5, 0.10), "stub": (4.0, 20.0, 5.0, 0.20)}
DEFAULTS = dict(local_daily_usd=10.0, web_daily_usd=1.0, web_all_daily_usd=5.0)      # the app's starting values; change them in Limits
MIN_START_USD = 0.02                       # below this left, a new question is not started (one round costs about this)
_lock = threading.Lock()


def _read(path, default):
    try:
        with open(path, encoding="utf-8") as f: return json.load(f)
    except (OSError, ValueError): return default


def _write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f: json.dump(obj, f, indent=1)
    os.replace(tmp, path)


def limits():
    v = dict(DEFAULTS); v.update({k: float(x) for k, x in (_read(LIMITS_FILE, {}) or {}).items() if k in DEFAULTS and x is not None})
    return v


def set_limits(new):
    cur = limits()
    for k, x in (new or {}).items():
        if k not in DEFAULTS: raise ValueError(f"no limit {k}")
        x = float(x)
        if not (x >= 0): raise ValueError(f"{k} must be zero or more")
        cur[k] = x
    _write(LIMITS_FILE, cur); return cur


def cost(model, usage):
    pi, po, pw, pr = PRICES.get(model, PRICES["claude-opus-5-5"])
    return (usage.get("input_tokens", 0) * pi + usage.get("output_tokens", 0) * po + usage.get("cache_write_tokens", 0) * pw
            + usage.get("cache_read_tokens", 0) * pr) / 1e6


def _today():
    return dt.date.today().isoformat()


def spent(client, day=None):
    led = _read(LEDGER_FILE, {}) or {}; d = (led.get("days") or {}).get(day or _today(), {})
    return float(d.get(client, 0.0)), float(sum(v for k, v in d.items() if k.startswith("web:")))


def remaining(client):
    """USD this client may still spend today (the smaller of its own and, for the web, all visitors' together)."""
    L = limits(); mine, web = spent(client)
    if client == "local": return max(0.0, L["local_daily_usd"] - mine)
    return max(0.0, min(L["web_daily_usd"] - mine, L["web_all_daily_usd"] - web))


def charge(client, usd):
    with _lock:
        led = _read(LEDGER_FILE, {}) or {}; days = led.setdefault("days", {})
        d = days.setdefault(_today(), {}); d[client] = round(float(d.get(client, 0.0)) + float(usd), 6)
        for k in sorted(days)[:-60]: days.pop(k)                    # two months kept
        _write(LEDGER_FILE, led)


def status(client):
    L = limits(); mine, web = spent(client)
    lim = L["local_daily_usd"] if client == "local" else L["web_daily_usd"]
    return dict(client="this computer" if client == "local" else "shared link visitor", spent_today_usd=round(mine, 4), limit_today_usd=lim,
                remaining_usd=round(remaining(client), 4), web_all_spent_today_usd=round(web, 4), limits=L if client == "local" else None)
