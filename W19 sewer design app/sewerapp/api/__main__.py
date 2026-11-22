"""Start the app: python -m sewerapp.api  (then open http://127.0.0.1:8765). Bound to this PC only."""
import uvicorn

if __name__ == "__main__":
    uvicorn.run("sewerapp.api.app:app", host="127.0.0.1", port=8765)
