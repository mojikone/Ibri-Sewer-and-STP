"""Start the app: python -m sewerapp.api  (then open http://127.0.0.1:8765). Bound to this PC only."""
import os
import uvicorn

if __name__ == "__main__":
    # open projects are kept on disk here so a reload or a restart finds them again (W19/work is not in git)
    os.environ.setdefault("W19_AUTOSAVE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "work", "sessions"))
    uvicorn.run("sewerapp.api.app:app", host="127.0.0.1", port=8765)
