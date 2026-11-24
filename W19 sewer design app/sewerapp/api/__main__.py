"""Start the app: python -m sewerapp.api  (then open http://127.0.0.1:8765). Bound to this PC only."""
import os
import uvicorn

if __name__ == "__main__":
    # open projects are kept on disk here so a reload or a restart finds them again (W19/work is not in git)
    os.environ.setdefault("W19_AUTOSAVE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work", "sessions"))
    # accounts (api/accounts.py): Cloudflare Access's settings and the accounts' projects, in the server's own folder
    # outside the repository (they hold email addresses)
    srv = os.path.join(os.environ.get("LOCALAPPDATA") or os.path.expanduser("~"), "w19_server")
    os.environ.setdefault("W19_ACCESS_CONFIG", os.path.join(srv, "access.json"))
    os.environ.setdefault("W19_ACCOUNTS_DIR", os.path.join(srv, "accounts"))
    uvicorn.run("sewerapp.api.app:app", host="127.0.0.1", port=8765)
